#!/usr/bin/env python3
"""Read-only preflight. Reports codes/structural locations, never field contents.

schema checks template shape; materials checks actual readiness independently of
saved booleans; upload also binds material digest to current session and draft.
The caller must observe the real UI. A JSON validator cannot authenticate it.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = "2026-09-05-v6"
PORTALS = {
    "domestic": ("recept.zjzwfw.gov.cn", "举办内地文艺表演团体、个人参加的营业性演出审批"),
    "foreign": ("whsq.mr.mct.gov.cn", "营业性演出（涉外/涉港澳台）"),
}
COMMON_QA = ("program_order_locked", "performer_count_matched", "all_paths_exist",
             "hashes_recorded", "cross_file_consistent", "slot_formats_valid",
             "document_owners_valid", "applicant_documents_match_policy",
             "signed_materials_checked", "no_duplicate_uploads")
QA = {
    "domestic": COMMON_QA + ("single_total_lyrics",),
    "foreign": COMMON_QA + ("entry_exit_dates_valid", "total_lyrics_first_program_only",
                           "session_count_consistent", "derived_files_visually_checked"),
}
RUNTIME = ("portal_matches_branch", "matter_matches", "target_draft_matches",
           "applicant_entity_matches_portal", "existing_rows_reconciled")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
OPTIONAL_FIELDS = {"translated_title", "group_name", "certificate_valid_to", "certificate_valid_from"}
FORMATS = {"video": {".mp4"}, "audio": {".mp3"}, "per_song_lyrics": {".docx"},
           "total_lyrics": {".docx"}, "performer_id": {".pdf", ".jpg", ".jpeg", ".png"},
           "fire_safety": {".pdf", ".jpg", ".jpeg", ".png"}}


def sha_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def material_digest(data):
    payload = {k: v for k, v in data.items()
               if k not in {"runtime_qa", "ready_for_upload", "ready_for_portal_check"}}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def value(field):
    return field.get("value") if isinstance(field, dict) else None


def positive_int(item):
    return type(item) is int and item > 0


def default_policy_path(skill_root=SKILL_ROOT):
    config = Path(skill_root) / "assets/config"
    candidates = [config / f"applicant-policy.{kind}.json" for kind in ("private", "local", "example")]
    return next((path for path in candidates if path.is_file()), candidates[-1])


class Validator:
    def __init__(self, data, json_path, stage="materials", session=None, draft=None, policy_path=None):
        self.data = data
        self.path = Path(json_path)
        self.stage = stage
        self.strict = stage != "schema"
        self.session, self.draft = session, draft
        self.policy_path = Path(policy_path) if policy_path else default_policy_path()
        self.errors = []
        self.attachments = []
        self.root = None
        self.branch = data.get("approval_branch")
        self.legal_name = None
        self.asset_pins = {}
        self.upload_ids = set()
        self.total_lyrics = []

    def error(self, code, location):
        self.errors.append((code, location))

    def field_map(self, fields, location):
        if not isinstance(fields, dict):
            self.error("E_FIELDS_OBJECT", location)
            return
        for idx, (name, field) in enumerate(fields.items()):
            loc = f"{location}.field[{idx}]"  # Never echo arbitrary input keys.
            if not isinstance(field, dict) or not all(k in field for k in ("semantic_type", "value", "source", "target_field")):
                self.error("E_COPY_FIELD_STRUCTURE", loc)
                continue
            for key in ("semantic_type", "target_field"):
                if not isinstance(field[key], str) or not field[key].strip():
                    self.error("E_COPY_FIELD_METADATA", loc)
            current = field["value"]
            if self.strict:
                if name not in OPTIONAL_FIELDS and (current is None or current == "" or current == []):
                    self.error("E_REQUIRED_FIELD_VALUE", loc)
                if current not in (None, "", []) and (not isinstance(field["source"], str) or not field["source"].strip()):
                    self.error("E_FIELD_SOURCE", loc)
                if "source_value" in field and field["source_value"] not in ("", current) and not field.get("mapping_reason"):
                    self.error("E_ENUM_MAPPING_REASON", loc)

    def required_fields(self, fields, names, location):
        if not isinstance(fields, dict):
            return
        for name in names:
            if name not in fields:
                self.error("E_REQUIRED_FIELD_MISSING", location + "." + name)

    def dated(self, field, location):
        raw = value(field)
        if not isinstance(raw, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            self.error("E_DATE_FORMAT", location)
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            self.error("E_DATE_VALUE", location)
            return None

    def items(self, items, location):
        if not isinstance(items, list):
            self.error("E_REQUIRED_LIST", location)
            return []
        if self.strict and not items:
            self.error("E_REQUIRED_NONEMPTY_LIST", location)
        keys = set()
        for idx, item in enumerate(items):
            loc = f"{location}[{idx}]"
            if not isinstance(item, dict):
                self.error("E_ITEM_OBJECT", loc)
                continue
            if type(item.get("sequence")) is not int or item["sequence"] != idx + 1:
                self.error("E_SEQUENCE_ORDER", loc)
            key = item.get("stable_key")
            if self.strict and (not isinstance(key, str) or not key.strip()):
                self.error("E_STABLE_KEY", loc)
            elif key and key in keys:
                self.error("E_DUPLICATE_STABLE_KEY", loc)
            if isinstance(key, str):
                keys.add(key)
        return [x for x in items if isinstance(x, dict)]

    def uploads(self, uploads, step, seq, location):
        if not isinstance(uploads, list):
            self.error("E_UPLOAD_ORDER_LIST", location)
            return []
        slot_counts, videos = {}, set()
        for idx, attachment in enumerate(uploads):
            loc = f"{location}[{idx}]"
            if not isinstance(attachment, dict):
                self.error("E_ATTACHMENT_OBJECT", loc)
                continue
            self.attachments.append(attachment)
            slot = attachment.get("slot")
            if not isinstance(slot, str) or not slot.strip():
                self.error("E_ATTACHMENT_SLOT", loc)
                continue
            slot_counts[slot] = slot_counts.get(slot, 0) + 1
            if type(attachment.get("sequence")) is not int or attachment["sequence"] != slot_counts[slot]:
                self.error("E_ATTACHMENT_SEQUENCE", loc)
            target = f"{self.branch}/{step}/{seq}/{slot}"
            if attachment.get("target_key") != target:
                self.error("E_ATTACHMENT_TARGET_CONTEXT", loc)
            method, kind = attachment.get("upload_method"), attachment.get("kind")
            if method not in {"local", "shared", "skill_asset"}:
                self.error("E_ATTACHMENT_METHOD", loc)
            if not isinstance(kind, str) or not kind:
                self.error("E_ATTACHMENT_KIND", loc)
            upload_id = attachment.get("upload_id")
            if not isinstance(upload_id, str) or not upload_id:
                self.error("E_ATTACHMENT_UPLOAD_ID", loc)
            elif upload_id in self.upload_ids:
                self.error("E_DUPLICATE_UPLOAD_ID", loc)
            else:
                self.upload_ids.add(upload_id)
            if kind == "total_lyrics":
                self.total_lyrics.append((step, seq))
            if kind == "video":
                identity = attachment.get("sha256")
                if isinstance(identity, str):
                    if identity in videos:
                        self.error("E_DUPLICATE_PROGRAM_VIDEO", loc)
                    videos.add(identity)
            if not isinstance(attachment.get("document_role"), str) or not attachment["document_role"]:
                self.error("E_ATTACHMENT_DOCUMENT_ROLE", loc)
            owner = attachment.get("document_owner_entity")
            if not isinstance(owner, str):
                self.error("E_ATTACHMENT_DOCUMENT_OWNER", loc)
            if self.strict and kind in {"fire_safety", "venue_consent", "venue_proof", "venue_business_license"} and (not isinstance(owner, str) or not owner.strip()):
                self.error("E_VENUE_DOCUMENT_OWNER_REQUIRED", loc)
            if self.strict and kind in {"applicant_license", "application_form", "authorization_letter"} and owner != self.legal_name:
                self.error("E_APPLICANT_DOCUMENT_OWNER", loc)
            if method == "shared":
                for key in ("shared_material_title", "shared_material_id", "document_owner_entity"):
                    if not isinstance(attachment.get(key), str) or not attachment[key].strip():
                        self.error("E_SHARED_METADATA", loc)
                if any(k in attachment for k in ("path", "asset_path", "sha256", "size_bytes")):
                    self.error("E_SHARED_FAKE_LOCAL_METADATA", loc)
                if upload_id != f"{target}:shared:{attachment.get('shared_material_id')}":
                    self.error("E_ATTACHMENT_UPLOAD_ID_MISMATCH", loc)
                continue
            if method not in {"local", "skill_asset"}:
                continue
            hash_value = attachment.get("sha256")
            if not isinstance(hash_value, str) or not SHA256.fullmatch(hash_value):
                self.error("E_ATTACHMENT_HASH_METADATA", loc)
            elif upload_id != f"{target}:{hash_value}":
                self.error("E_ATTACHMENT_UPLOAD_ID_MISMATCH", loc)
            if not positive_int(attachment.get("size_bytes")):
                self.error("E_ATTACHMENT_SIZE_METADATA", loc)
            if not isinstance(attachment.get("derived_from"), str):
                self.error("E_ATTACHMENT_DERIVED_FROM", loc)
            path_key = "asset_path" if method == "skill_asset" else "path"
            raw_path = attachment.get(path_key)
            if not isinstance(raw_path, str) or not raw_path.strip() or Path(raw_path).is_absolute():
                self.error("E_ATTACHMENT_RELATIVE_PATH", loc)
                continue
            if self.strict:
                root = SKILL_ROOT if method == "skill_asset" else self.root
                if method == "skill_asset":
                    pin = self.asset_pins.get(raw_path)
                    if not isinstance(pin, dict) or any(pin.get(key) != attachment.get(key) for key in ("sha256", "size_bytes", "slot", "kind")) or pin.get("approval_branch") != self.branch:
                        self.error("E_SKILL_ASSET_PIN_MISMATCH", loc)
                if root is None:
                    continue
                try:
                    resolved = (root / raw_path).resolve(strict=True)
                    resolved.relative_to(root)
                    if not resolved.is_file():
                        raise OSError()
                except (ValueError, OSError, RuntimeError):
                    self.error("E_ATTACHMENT_MISSING_OR_OUTSIDE_ROOT", loc)
                    continue
                if attachment.get("filename") != resolved.name:
                    self.error("E_ATTACHMENT_FILENAME_MISMATCH", loc)
                if attachment.get("size_bytes") != resolved.stat().st_size:
                    self.error("E_ATTACHMENT_SIZE_MISMATCH", loc)
                if hash_value != sha_file(resolved):
                    self.error("E_ATTACHMENT_HASH_MISMATCH", loc)
                if kind in FORMATS and resolved.suffix.lower() not in FORMATS[kind]:
                    self.error("E_SLOT_FORMAT", loc)
                if attachment.get("derived_from"):
                    try:
                        origin = (self.root / attachment["derived_from"]).resolve(strict=True)
                        origin.relative_to(self.root)
                        if not origin.is_file():
                            raise OSError()
                    except (TypeError, ValueError, OSError, RuntimeError):
                        self.error("E_DERIVED_SOURCE", loc)
        return [x for x in uploads if isinstance(x, dict)]

    def validate(self):
        d = self.data
        if d.get("schema_version") != SCHEMA_VERSION:
            self.error("E_SCHEMA_MIGRATION_REQUIRED", "$.schema_version")
        if self.branch not in PORTALS:
            self.error("E_APPROVAL_BRANCH", "$.approval_branch")
            return self.errors
        portal = d.get("portal", {})
        if not isinstance(portal, dict):
            portal = {}
        if (portal.get("host"), portal.get("matter")) != PORTALS[self.branch]:
            self.error("E_PORTAL_BRANCH_MISMATCH", "$.portal")
        if not isinstance(portal.get("page_markers"), list) or not portal["page_markers"]:
            self.error("E_PORTAL_MARKERS", "$.portal")
        for key in ("ready_for_portal_check", "ready_for_upload"):
            if type(d.get(key)) is not bool:
                self.error("E_READINESS_TYPE", "$." + key)
        warnings = d.get("warnings")
        if not isinstance(warnings, list):
            self.error("E_WARNINGS_LIST", "$.warnings")
        elif self.strict and warnings:
            self.error("E_UNRESOLVED_WARNINGS", "$.warnings")
        raw_root = d.get("project_root")
        if not isinstance(raw_root, str) or not raw_root.strip():
            self.error("E_PROJECT_ROOT", "$.project_root")
        elif self.strict:
            try:
                root = Path(raw_root).expanduser()
                self.root = (root if root.is_absolute() else self.path.parent / root).resolve(strict=True)
                if not self.root.is_dir():
                    raise OSError()
                self.path.resolve().relative_to(self.root)
            except (ValueError, OSError, RuntimeError):
                self.error("E_PROJECT_ROOT", "$.project_root")
                self.root = None
        if self.strict:
            try:
                configuration = json.loads(self.policy_path.read_text(encoding="utf-8"))
                policy = configuration["applicant_policy"]
                self.legal_name = policy["legal_name"]
                self.asset_pins = configuration.get("asset_pins", {})
                if not isinstance(self.asset_pins, dict):
                    raise ValueError()
                if not isinstance(self.legal_name, str) or not self.legal_name.strip() or set(policy["applies_to"]) != set(PORTALS):
                    raise ValueError()
            except (OSError, ValueError, KeyError, TypeError):
                self.error("E_APPLICANT_POLICY_UNCONFIGURED", "policy")
        app = d.get("application")
        self.field_map(app, "$.application")
        app = app if isinstance(app, dict) else {}
        self.required_fields(app, ("applicant_entity", "event_name"), "$.application")
        if "expected_applicant_entity" in app:
            self.error("E_LEGACY_APPLICANT_FIELD", "$.application")
        if self.strict and value(app.get("applicant_entity")) != self.legal_name:
            self.error("E_APPLICANT_POLICY_CONFLICT", "$.application.applicant_entity")
        for qa_name in QA[self.branch]:
            qa = d.get("qa", {})
            if not isinstance(qa, dict) or type(qa.get(qa_name)) is not bool:
                self.error("E_QA_BOOLEAN", "$.qa." + qa_name)
            elif self.strict and qa[qa_name] is not True:
                self.error("E_MATERIAL_QA_INCOMPLETE", "$.qa." + qa_name)
        performers = self.items(d.get("performers"), "$.performers")
        categories, certificates = [], set()
        for idx, performer in enumerate(performers):
            loc = f"$.performers[{idx}]"
            self.field_map({"performer_category": performer.get("performer_category")}, loc)
            category = value(performer.get("performer_category"))
            categories.append(category)
            if category not in {"mainland", "non_mainland"}:
                self.error("E_PERFORMER_CATEGORY", loc)
            fields = performer.get("fields")
            self.field_map(fields, loc + ".fields")
            fields = fields if isinstance(fields, dict) else {}
            self.required_fields(fields, ("name", "certificate_type", "certificate_number", "role", "birth_date"), loc)
            if self.strict:
                identity = (value(fields.get("certificate_type")), value(fields.get("certificate_number")))
                if all(isinstance(x, str) and x for x in identity):
                    if identity in certificates:
                        self.error("E_DUPLICATE_PERFORMER_IDENTITY", loc)
                    certificates.add(identity)
                self.dated(fields.get("birth_date"), loc + ".birth_date")
                long_term = value(fields.get("certificate_long_term")) is True
                if not long_term:
                    end = self.dated(fields.get("certificate_valid_to"), loc + ".certificate_valid_to")
                    start_field = fields.get("certificate_valid_from")
                    if value(start_field):
                        start = self.dated(start_field, loc + ".certificate_valid_from")
                        if start and end and end < start:
                            self.error("E_CERTIFICATE_DATE_ORDER", loc)
            person_uploads = self.uploads(performer.get("upload_order"), "performer", idx + 1, loc + ".upload_order")
            if self.strict:
                kinds = [a.get("kind") for a in person_uploads]
                if kinds.count("performer_id") != 1 or kinds.count("performance_agreement") != 1:
                    self.error("E_PERFORMER_REQUIRED_ATTACHMENTS", loc)
                if value(fields.get("is_minor")) is True and "guardian_consent" not in kinds:
                    self.error("E_GUARDIAN_CONSENT_REQUIRED", loc)
        if self.strict and ((self.branch == "domestic" and any(x != "mainland" for x in categories)) or
                            (self.branch == "foreign" and "non_mainland" not in categories)):
            self.error("E_PERFORMER_BRANCH_MISMATCH", "$.performers")
        programs = self.items(d.get("programs"), "$.programs")
        for idx, program in enumerate(programs):
            loc = f"$.programs[{idx}]"
            fields = {k: v for k, v in program.items() if k not in {"sequence", "stable_key", "upload_order"}}
            self.field_map(fields, loc)
            self.required_fields(fields, ("display_name" if self.branch == "domestic" else "title", "program_type"), loc)
            uploads = self.uploads(program.get("upload_order"), "program", idx + 1, loc + ".upload_order")
            if self.strict:
                kinds = [a.get("kind") for a in uploads]
                if self.branch == "domestic" and kinds.count("video") != 1:
                    self.error("E_DOMESTIC_PROGRAM_VIDEO_COUNT", loc)
                if self.branch == "foreign" and (kinds.count("per_song_lyrics") != 1 or kinds.count("audio") != 1):
                    self.error("E_FOREIGN_PROGRAM_REQUIRED_ATTACHMENTS", loc)
        if self.branch == "domestic":
            if any(k in app for k in ("entry_date", "exit_date")) or "venue" in d:
                self.error("E_DOMESTIC_FOREIGN_FIELD", "$")
            plans = self.items(d.get("performance_plans"), "$.performance_plans")
            for idx, plan in enumerate(plans):
                loc = f"$.performance_plans[{idx}]"
                fields = plan.get("fields")
                self.field_map(fields, loc + ".fields")
                fields = fields if isinstance(fields, dict) else {}
                self.required_fields(fields, ("event_start_date", "event_end_date", "session_count", "venue_operator_entity", "venue_name", "venue_address"), loc)
                if self.strict:
                    start = self.dated(fields.get("event_start_date"), loc)
                    end = self.dated(fields.get("event_end_date"), loc)
                    if start and end and end < start:
                        self.error("E_EVENT_DATE_ORDER", loc)
                    if not positive_int(value(fields.get("session_count"))):
                        self.error("E_SESSION_COUNT", loc)
                venue_uploads = self.uploads(plan.get("upload_order"), "plan", idx + 1, loc + ".upload_order")
                if self.strict and sum(x.get("kind") == "venue_proof" for x in venue_uploads) != 1:
                    self.error("E_DOMESTIC_VENUE_PROOF_REQUIRED", loc)
            materials = self.uploads(d.get("material_uploads"), "materials", 1, "$.material_uploads")
            if self.strict:
                kinds = [a.get("kind") for a in materials]
                for kind in ("application_form", "program_list", "performer_list", "applicant_license", "authorization_letter"):
                    if kinds.count(kind) != 1:
                        self.error("E_DOMESTIC_REQUIRED_MATERIAL", "$.material_uploads")
            if self.strict and self.total_lyrics != [("materials", 1)]:
                self.error("E_DOMESTIC_TOTAL_LYRICS_LOCATION", "$.material_uploads")
        else:
            if "performance_plans" in d or "material_uploads" in d:
                self.error("E_FOREIGN_DOMESTIC_FIELD", "$")
            self.foreign(app)
            if self.strict and self.total_lyrics != [("program", 1)]:
                self.error("E_FOREIGN_TOTAL_LYRICS_LOCATION", "$.programs")
        self.runtime()
        return self.errors

    def foreign(self, app):
        venue = self.data.get("venue")
        if not isinstance(venue, dict):
            self.error("E_VENUE_OBJECT", "$.venue")
            return
        fields = venue.get("fields")
        self.field_map(fields, "$.venue.fields")
        self.required_fields(fields, ("venue_name", "venue_operator_entity", "venue_address"), "$.venue")
        venue_uploads = self.uploads(venue.get("upload_order"), "venue", 1, "$.venue.upload_order")
        requirement = venue.get("fire_safety_requirement")
        if not isinstance(requirement, dict) or type(requirement.get("required")) is not bool or not isinstance(requirement.get("source"), str) or not requirement["source"].strip():
            self.error("E_FIRE_SAFETY_REQUIREMENT", "$.venue")
        if self.strict:
            kinds = [x.get("kind") for x in venue_uploads]
            if kinds.count("venue_consent") != 1:
                self.error("E_FOREIGN_VENUE_CONSENT_REQUIRED", "$.venue.upload_order")
            if isinstance(requirement, dict) and type(requirement.get("required")) is bool:
                if kinds.count("fire_safety") != int(requirement["required"]):
                    self.error("E_FIRE_SAFETY_ATTACHMENT_COUNT", "$.venue.upload_order")
        sessions = self.items(venue.get("sessions"), "$.venue.sessions")
        event_start = event_end = None
        if self.strict:
            event_start = self.dated(app.get("event_start_date"), "$.application.event_start_date")
            event_end = self.dated(app.get("event_end_date"), "$.application.event_end_date")
            entry = self.dated(app.get("entry_date"), "$.application.entry_date")
            exit_date = self.dated(app.get("exit_date"), "$.application.exit_date")
            if all((event_start, event_end, entry, exit_date)):
                if not entry <= event_start <= event_end <= exit_date:
                    self.error("E_ENTRY_EVENT_EXIT_ORDER", "$.application")
                basis = value(app.get("entry_exit_basis"))
                if basis == "computed_10_days":
                    if entry != event_start - timedelta(days=10) or exit_date != event_end + timedelta(days=10):
                        self.error("E_ENTRY_EXIT_COMPUTATION", "$.application")
                elif basis != "material_explicit":
                    self.error("E_ENTRY_EXIT_BASIS", "$.application.entry_exit_basis")
        seen = set()
        for idx, session in enumerate(sessions):
            loc = f"$.venue.sessions[{idx}]"
            self.field_map({k: session.get(k) for k in ("date", "start_time", "end_time")}, loc)
            if self.strict:
                day = self.dated(session.get("date"), loc + ".date")
                times = [value(session.get(k)) for k in ("start_time", "end_time")]
                if not all(isinstance(x, str) and re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", x) for x in times):
                    self.error("E_SESSION_TIME", loc)
                elif times[0] >= times[1]:
                    self.error("E_SESSION_TIME_ORDER", loc)
                if day and event_start and event_end and not event_start <= day <= event_end:
                    self.error("E_SESSION_OUTSIDE_EVENT", loc)
                identity = (str(day), str(times))
                if identity in seen:
                    self.error("E_DUPLICATE_SESSION", loc)
                seen.add(identity)
                if type(session.get("represented_session_count")) is not int or session["represented_session_count"] != 1:
                    self.error("E_ONE_ROW_ONE_SESSION", loc)
        if self.strict and (not positive_int(venue.get("declared_session_count")) or venue["declared_session_count"] != len(sessions)):
            self.error("E_FOREIGN_SESSION_COUNT", "$.venue")

    def runtime(self):
        runtime = self.data.get("runtime_qa")
        if not isinstance(runtime, dict):
            self.error("E_RUNTIME_QA_OBJECT", "$.runtime_qa")
            return
        for key in RUNTIME:
            if type(runtime.get(key)) is not bool:
                self.error("E_RUNTIME_QA_BOOLEAN", "$.runtime_qa." + key)
        if self.stage != "upload":
            return
        for key in ("ready_for_portal_check", "ready_for_upload"):
            if self.data.get(key) is not True:
                self.error("E_READINESS_NOT_ATTESTED", "$." + key)
        for key in RUNTIME:
            if runtime.get(key) is not True:
                self.error("E_RUNTIME_QA_INCOMPLETE", "$.runtime_qa." + key)
        for key, current in (("portal_session_fingerprint", self.session), ("draft_fingerprint", self.draft)):
            if not isinstance(current, str) or not SHA256.fullmatch(current):
                self.error("E_CURRENT_CONTEXT_REQUIRED", "runtime." + key)
            elif runtime.get(key) != current:
                self.error("E_RUNTIME_CONTEXT_CHANGED", "$.runtime_qa." + key)
        if runtime.get("materials_sha256") != material_digest(self.data):
            self.error("E_MATERIALS_CHANGED", "$.runtime_qa.materials_sha256")
        if runtime.get("observed_applicant_entity") != self.legal_name or not runtime.get("applicant_evidence_source"):
            self.error("E_RUNTIME_APPLICANT_EVIDENCE", "$.runtime_qa")
        try:
            checked = datetime.fromisoformat(runtime.get("checked_at", "").replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - checked
            if checked.tzinfo is None or not timedelta(minutes=-1) <= age <= timedelta(minutes=30):
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            self.error("E_RUNTIME_CHECK_EXPIRED", "$.runtime_qa.checked_at")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--stage", choices=("schema", "materials", "upload"), default="materials")
    parser.add_argument("--session-fingerprint")
    parser.add_argument("--draft-fingerprint")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.json_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError()
    except (OSError, ValueError, UnicodeError):
        print("[ERROR] E_JSON_READ_OR_STRUCTURE @ input")
        return 1
    validator = Validator(data, args.json_path, args.stage, args.session_fingerprint, args.draft_fingerprint)
    try:
        validator.validate()
    except (OSError, TypeError, ValueError, OverflowError):
        validator.error("E_INVALID_INPUT_TYPE_OR_UNREADABLE_FILE", "input")
    for code, location in validator.errors:
        print(f"[ERROR] {code} @ {location}")
    print(f"SUMMARY stage={args.stage} errors={len(validator.errors)} attachments={len(validator.attachments)}")
    if validator.errors:
        print("RESULT BLOCKED")
        return 1
    if args.stage == "schema":
        print("RESULT SCHEMA_VALID_ONLY_NOT_READY_FOR_UPLOAD")
    else:
        print("MATERIALS_SHA256 " + material_digest(data))
        print("RESULT MATERIALS_VALID_REQUIRES_CURRENT_PORTAL_CHECK" if args.stage == "materials"
              else "RESULT UPLOAD_PREFLIGHT_VALID_REQUIRES_OBSERVED_CURRENT_UI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
