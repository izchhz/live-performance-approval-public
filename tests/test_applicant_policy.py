"""Synthetic applicant-policy regression tests; no private assets are used."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skill/live-performance-approval/scripts'))
from applicant_policy import load_company_config, migrate_manifest, subject_issues
from project_manifest import build_manifest


class ApplicantPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.config = json.loads((ROOT / 'skill/live-performance-approval/assets/config/company-profile.example.json').read_text())
        self.config['companies']['applicant_a'].update({
            'legal_name': 'Synthetic Applicant Ltd',
            'performance_license_no': 'SYNTHETIC-LICENSE',
            'registered_address': 'Synthetic registered address',
            'seal_path': 'assets/seals/synthetic.png',
            'business_license_path': 'assets/fixed-documents/synthetic.docx',
        })
        self.path = self.directory / 'company.json'
        self.save_config()

    def save_config(self):
        self.path.write_text(json.dumps(self.config))

    def manifest(self, branch='domestic'):
        return build_manifest(self.directory, 'Synthetic Event', '2026-11-13 20:00-22:00',
                              config_path=self.path, approval_type=branch)

    def test_same_applicant_across_branches(self):
        self.assertEqual(self.manifest()['application_subject'], self.manifest('foreign')['application_subject'])

    def test_auto_does_not_claim_a_branch_or_authority(self):
        workflow = self.manifest('auto')['workflow']
        self.assertEqual(workflow['approval_type'], 'auto')
        self.assertEqual(workflow['approval_authority'], '')
        self.assertFalse(workflow['locked']['project_master'])

    def test_public_placeholders_cannot_initialize(self):
        with self.assertRaises(ValueError):
            load_company_config(ROOT / 'skill/live-performance-approval/assets/config/company-profile.example.json')

    def test_conflicting_branch_applicant_fails(self):
        self.config['foreign']['applicant_company_key'] = 'venue_a'
        self.save_config()
        with self.assertRaises(ValueError):
            self.manifest()

    def test_old_subject_fails_current_policy(self):
        manifest = self.manifest()
        manifest['application_subject']['company'] = 'Synthetic Previous Applicant'
        self.assertTrue(subject_issues(manifest, self.config))

    def test_migration_invalidates_outputs_without_deleting_them(self):
        manifest = self.manifest()
        manifest['application_subject']['company'] = 'Synthetic Previous Applicant'
        manifest['documents']['04'].update(status='complete', outputs=['consent.pdf'])
        manifest['ready_for_upload'] = True
        migrate_manifest(manifest, self.config)
        self.assertEqual(manifest['documents']['04']['status'], 'stale')
        self.assertEqual(manifest['documents']['04']['outputs'], ['consent.pdf'])
        self.assertFalse(manifest['ready_for_upload'])
        self.assertEqual(manifest['migration_history'][0]['previous_subject']['company'], 'Synthetic Previous Applicant')
        self.assertEqual(subject_issues(manifest, self.config), [])

    def test_current_policy_migration_is_idempotent(self):
        manifest = self.manifest()
        before = copy.deepcopy(manifest)
        self.assertEqual(migrate_manifest(manifest, self.config), before)


if __name__ == '__main__':
    unittest.main()
