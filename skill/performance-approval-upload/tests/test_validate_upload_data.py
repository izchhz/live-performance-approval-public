"""Offline contract regressions; all identities/files are fabricated in temp dirs."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("upload_validator", ROOT / "scripts/validate_upload_data.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class UploadValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input_path = self.root / "input.json"
        self.policy_path = self.root / "policy.json"
        self.policy_path.write_text(json.dumps({"applicant_policy": {
            "legal_name": "示例申报企业", "applies_to": ["domestic", "foreign"]}}))

    def attachment(self, branch, step, kind, suffix=".pdf", sequence=1, slot=None):
        slot = slot or kind
        filename = kind + suffix
        payload = ("synthetic fixture " + kind).encode()
        (self.root / filename).write_bytes(payload)
        target = f"{branch}/{step}/1/{slot}"
        digest = hashlib.sha256(payload).hexdigest()
        return {"target_key": target, "slot": slot, "kind": kind, "sequence": sequence,
                "upload_method": "local", "path": filename, "filename": filename,
                "size_bytes": len(payload), "sha256": digest, "document_role": kind,
                "document_owner_entity": "示例申报企业", "derived_from": "",
                "upload_id": target + ":" + digest}

    def fixture(self, branch):
        data = json.loads((ROOT / "assets" / f"{branch}-upload-template.json").read_text())
        def fill(node):
            if isinstance(node, dict):
                if "semantic_type" in node:
                    if node["value"] in ("", []):
                        node["value"] = "示例值"
                    node["source"] = "synthetic material source"
                for key, child in node.items():
                    if key == "stable_key":
                        node[key] = "synthetic-key"
                    else:
                        fill(child)
            elif isinstance(node, list):
                for child in node:
                    fill(child)
        fill(data)
        data["application"]["applicant_entity"]["value"] = "示例申报企业"
        data["qa"] = {name: True for name in v.QA[branch]}
        person = data["performers"][0]
        person["fields"]["birth_date"]["value"] = "1990-01-01"
        person["fields"]["certificate_valid_from"]["value"] = "2020-01-01"
        person["fields"]["certificate_valid_to"]["value"] = "2035-01-01"
        person["upload_order"] = [self.attachment(branch, "performer", kind)
                                  for kind in ("performer_id", "performance_agreement")]
        if branch == "domestic":
            plan = data["performance_plans"][0]
            plan["fields"]["event_start_date"]["value"] = "2026-12-31"
            plan["fields"]["event_end_date"]["value"] = "2026-12-31"
            plan["upload_order"] = [self.attachment(branch, "plan", "venue_proof")]
            data["programs"][0]["upload_order"] = [self.attachment(branch, "program", "video", ".mp4")]
            data["material_uploads"] = [self.attachment(branch, "materials", kind)
                for kind in ("application_form", "program_list", "performer_list", "applicant_license", "authorization_letter")]
            data["material_uploads"].append(self.attachment(branch, "materials", "total_lyrics", ".docx"))
        else:
            app = data["application"]
            for key, day in (("event_start_date", "2026-12-31"), ("event_end_date", "2027-01-02"),
                             ("entry_date", "2026-12-21"), ("exit_date", "2027-01-12")):
                app[key]["value"] = day
            data["venue"]["upload_order"] = [self.attachment(branch, "venue", "venue_consent")]
            data["venue"]["fire_safety_requirement"] = {"required": False, "source": "synthetic page requirement"}
            session = data["venue"]["sessions"][0]
            for key, val in (("date", "2026-12-31"), ("start_time", "19:00"), ("end_time", "21:00")):
                session[key]["value"] = val
            data["programs"][0]["upload_order"] = [self.attachment(branch, "program", kind, suffix)
                for kind, suffix in (("per_song_lyrics", ".docx"), ("audio", ".mp3"), ("total_lyrics", ".docx"))]
        self.input_path.write_text(json.dumps(data))
        return data

    def errors(self, data, stage="materials", session=None, draft=None):
        val = v.Validator(data, self.input_path, stage, session, draft, self.policy_path)
        return {code for code, _ in val.validate()}

    def ready(self, data):
        data["ready_for_portal_check"] = data["ready_for_upload"] = True
        runtime = data["runtime_qa"]
        runtime.update({key: True for key in v.RUNTIME})
        runtime.update({"checked_at": datetime.now(timezone.utc).isoformat(),
                        "portal_session_fingerprint": "a" * 64, "draft_fingerprint": "b" * 64,
                        "observed_applicant_entity": "示例申报企业", "applicant_evidence_source": "synthetic company page"})
        runtime["materials_sha256"] = v.material_digest(data)

    def test_complete_domestic_and_foreign_materials_pass(self):
        for branch in v.PORTALS:
            with self.subTest(branch=branch):
                self.assertEqual(set(), self.errors(self.fixture(branch)))

    def test_empty_templates_only_pass_schema(self):
        for branch in v.PORTALS:
            data = json.loads((ROOT / "assets" / f"{branch}-upload-template.json").read_text())
            self.assertEqual(set(), self.errors(data, "schema"))
            self.assertIn("E_REQUIRED_FIELD_VALUE", self.errors(data))
            data["ready_for_portal_check"] = False
            self.assertIn("E_MATERIAL_QA_INCOMPLETE", self.errors(data))

    def test_unified_entity_conflict_in_both_branches(self):
        for branch in v.PORTALS:
            data = self.fixture(branch)
            data["application"]["applicant_entity"]["value"] = "历史示例企业"
            self.assertIn("E_APPLICANT_POLICY_CONFLICT", self.errors(data))

    def test_foreign_missing_actual_company_evidence_rejected(self):
        data = self.fixture("foreign")
        self.ready(data)
        data["runtime_qa"]["observed_applicant_entity"] = ""
        self.assertIn("E_RUNTIME_APPLICANT_EVIDENCE", self.errors(data, "upload", "a"*64, "b"*64))

    def test_materials_change_invalidates_context(self):
        data = self.fixture("domestic")
        self.ready(data)
        self.assertEqual(set(), self.errors(data, "upload", "a"*64, "b"*64))
        data["application"]["event_name"]["value"] = "revised synthetic event"
        self.assertIn("E_MATERIALS_CHANGED", self.errors(data, "upload", "a"*64, "b"*64))

    def test_session_draft_and_age_are_checked(self):
        data = self.fixture("foreign")
        self.ready(data)
        self.assertIn("E_CURRENT_CONTEXT_REQUIRED", self.errors(data, "upload"))
        self.assertIn("E_RUNTIME_CONTEXT_CHANGED", self.errors(data, "upload", "c"*64, "b"*64))
        data["runtime_qa"]["checked_at"] = (datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()
        self.assertIn("E_RUNTIME_CHECK_EXPIRED", self.errors(data, "upload", "a"*64, "b"*64))

    def test_cross_year_dates_and_explicit_override(self):
        data = self.fixture("foreign")
        data["application"]["exit_date"]["value"] = "2027-01-11"
        self.assertIn("E_ENTRY_EXIT_COMPUTATION", self.errors(data))
        data["application"]["entry_exit_basis"]["value"] = "material_explicit"
        self.assertEqual(set(), self.errors(data))

    def test_invalid_and_reversed_dates(self):
        data = self.fixture("foreign")
        data["application"]["event_start_date"]["value"] = "2026-02-30"
        self.assertIn("E_DATE_VALUE", self.errors(data))
        data = self.fixture("domestic")
        data["performance_plans"][0]["fields"]["event_end_date"]["value"] = "2026-01-01"
        self.assertIn("E_EVENT_DATE_ORDER", self.errors(data))

    def test_wrong_branch_and_performer_identity_rejected(self):
        data = self.fixture("domestic")
        data["performers"][0]["performer_category"]["value"] = "non_mainland"
        self.assertIn("E_PERFORMER_BRANCH_MISMATCH", self.errors(data))
        data["portal"]["host"] = v.PORTALS["foreign"][0]
        self.assertIn("E_PORTAL_BRANCH_MISMATCH", self.errors(data))

    def test_duplicate_and_wrong_window_upload_rejected(self):
        data = self.fixture("domestic")
        uploads = data["programs"][0]["upload_order"]
        uploads.append(copy.deepcopy(uploads[0]))
        self.assertIn("E_DUPLICATE_UPLOAD_ID", self.errors(data))
        self.assertIn("E_DUPLICATE_PROGRAM_VIDEO", self.errors(data))
        uploads.pop()
        uploads[0]["target_key"] = "foreign/program/1/video"
        self.assertIn("E_ATTACHMENT_TARGET_CONTEXT", self.errors(data))

    def test_file_tampering_and_escape_rejected(self):
        data = self.fixture("domestic")
        attachment = data["programs"][0]["upload_order"][0]
        (self.root / attachment["path"]).write_bytes(b"changed")
        self.assertIn("E_ATTACHMENT_HASH_MISMATCH", self.errors(data))
        attachment["path"] = "../outside.mp4"
        self.assertIn("E_ATTACHMENT_MISSING_OR_OUTSIDE_ROOT", self.errors(data))

    def test_shared_upload_id_and_ownership(self):
        data = self.fixture("domestic")
        shared = data["material_uploads"][3]
        for key in ("path", "filename", "size_bytes", "sha256", "derived_from"):
            shared.pop(key)
        shared.update({"upload_method": "shared", "shared_material_title": "synthetic license", "shared_material_id": "fixture-1"})
        shared["upload_id"] = shared["target_key"] + ":shared:fixture-1"
        self.assertEqual(set(), self.errors(data))
        shared["document_owner_entity"] = "historical synthetic owner"
        shared["upload_id"] = "wrong"
        self.assertIn("E_APPLICANT_DOCUMENT_OWNER", self.errors(data))
        self.assertIn("E_ATTACHMENT_UPLOAD_ID_MISMATCH", self.errors(data))

    def test_skill_asset_upload_id_verified_in_schema(self):
        data = json.loads((ROOT / "assets/foreign-upload-template.json").read_text())
        asset = self.attachment("foreign", "venue", "fire_safety")
        asset["upload_method"] = "skill_asset"
        asset["asset_path"] = "assets/synthetic-fire-safety.pdf"
        asset.pop("path")
        asset["upload_id"] = "wrong"
        data["venue"]["upload_order"] = [asset]
        self.assertIn("E_ATTACHMENT_UPLOAD_ID_MISMATCH", self.errors(data, "schema"))

    def test_sequence_order_total_lyrics_and_sessions(self):
        data = self.fixture("foreign")
        data["programs"][0]["sequence"] = 2
        data["programs"][0]["upload_order"].pop()
        data["venue"]["declared_session_count"] = 2
        errors = self.errors(data)
        self.assertTrue({"E_SEQUENCE_ORDER", "E_FOREIGN_TOTAL_LYRICS_LOCATION", "E_FOREIGN_SESSION_COUNT"} <= errors)

    def test_missing_performer_and_global_materials_rejected(self):
        data = self.fixture("domestic")
        data["performers"][0]["upload_order"] = []
        data["material_uploads"] = []
        errors = self.errors(data)
        self.assertIn("E_PERFORMER_REQUIRED_ATTACHMENTS", errors)
        self.assertIn("E_DOMESTIC_REQUIRED_MATERIAL", errors)

    def test_public_unconfigured_policy_fails_closed(self):
        data = self.fixture("foreign")
        self.policy_path.write_text('{"applicant_policy":{"legal_name":"","applies_to":["domestic","foreign"]}}')
        self.assertIn("E_APPLICANT_POLICY_UNCONFIGURED", self.errors(data))

    def test_missing_venue_and_empty_fire_owner_are_rejected(self):
        data = self.fixture("foreign")
        data["venue"]["upload_order"] = []
        self.assertIn("E_FOREIGN_VENUE_CONSENT_REQUIRED", self.errors(data))
        data = self.fixture("domestic")
        data["performance_plans"][0]["upload_order"] = []
        self.assertIn("E_DOMESTIC_VENUE_PROOF_REQUIRED", self.errors(data))
        data = self.fixture("foreign")
        data["venue"]["fire_safety_requirement"]["required"] = True
        self.assertIn("E_FIRE_SAFETY_ATTACHMENT_COUNT", self.errors(data))
        fire = self.attachment("foreign", "venue", "fire_safety")
        fire["document_owner_entity"] = ""
        data["venue"]["upload_order"].append(fire)
        self.assertIn("E_VENUE_DOCUMENT_OWNER_REQUIRED", self.errors(data))

    def test_skill_asset_content_is_bound_to_config_pin(self):
        data = self.fixture("foreign")
        data["venue"]["fire_safety_requirement"]["required"] = True
        fire = self.attachment("foreign", "venue", "fire_safety")
        fire["upload_method"] = "skill_asset"
        fire["asset_path"] = fire.pop("path")
        data["venue"]["upload_order"].append(fire)
        configuration = json.loads(self.policy_path.read_text())
        configuration["asset_pins"] = {fire["asset_path"]: {k: fire[k] for k in ("sha256", "size_bytes", "kind", "slot")}}
        configuration["asset_pins"][fire["asset_path"]]["approval_branch"] = "foreign"
        self.policy_path.write_text(json.dumps(configuration))
        with patch.object(v, "SKILL_ROOT", self.root.resolve()):
            self.assertEqual(set(), self.errors(data))
            payload = b"a changed asset with recomputed project metadata"
            (self.root / fire["asset_path"]).write_bytes(payload)
            fire["sha256"] = hashlib.sha256(payload).hexdigest()
            fire["size_bytes"] = len(payload)
            fire["upload_id"] = fire["target_key"] + ":" + fire["sha256"]
            self.assertIn("E_SKILL_ASSET_PIN_MISMATCH", self.errors(data))

    def test_policy_lookup_prefers_private_then_local_then_example(self):
        config = self.root / "assets/config"
        config.mkdir(parents=True)
        for kind in ("example", "local", "private"):
            path = config / f"applicant-policy.{kind}.json"
            path.write_text("{}")
            self.assertEqual(path, v.default_policy_path(self.root))

    def test_cli_bad_types_and_values_do_not_leak(self):
        data = self.fixture("domestic")
        sentinel = "SENSITIVE-FIXTURE-DO-NOT-PRINT"
        data["application"]["event_name"]["value"] = sentinel
        data["approval_branch"] = [sentinel]
        self.input_path.write_text(json.dumps(data))
        output = subprocess.run([sys.executable, str(ROOT / "scripts/validate_upload_data.py"), str(self.input_path)], text=True, capture_output=True)
        self.assertEqual(1, output.returncode)
        self.assertNotIn(sentinel, output.stdout + output.stderr)
        self.assertNotIn("Traceback", output.stderr)


if __name__ == "__main__":
    unittest.main()
