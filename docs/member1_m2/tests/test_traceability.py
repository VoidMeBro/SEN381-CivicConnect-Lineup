import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from traceability import validate, render, changes_for, verify_manifest
import hashlib

class TraceabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        pack=Path(__file__).resolve().parents[1]
        self.rows=json.loads((pack/'rtm.json').read_text(encoding='utf-8'))
        (self.root/'baseline_m1.json').write_bytes((pack/'baseline_m1.json').read_bytes())
        for r in self.rows:
            for key in ('implementation','verification'):
                for link in r[key]:
                    f=self.root/link; f.parent.mkdir(parents=True,exist_ok=True); f.write_text('fixture')
    def check(self):
        (self.root/'rtm.json').write_text(json.dumps(self.rows),encoding='utf-8')
        return validate(self.root)
    def test_valid_preserved_baseline(self): self.assertEqual(self.check(),[])
    def test_missing_requirement(self):
        self.rows.pop(); self.assertTrue(any('coverage' in x for x in self.check()))
    def test_duplicate_id(self):
        self.rows.append(copy.deepcopy(self.rows[0])); self.assertTrue(any('Duplicate' in x for x in self.check()))
    def test_unproven_implementation(self):
        self.rows[0]['status']='Implemented'; self.assertTrue(any('Implemented needs' in x for x in self.check()))
    def test_broken_link(self):
        self.rows[0]['implementation']=['missing.py']; self.assertTrue(any('missing evidence' in x for x in self.check()))
    def test_path_escape(self):
        self.rows[0]['implementation']=['../outside']; self.assertTrue(any('escapes' in x for x in self.check()))
    def test_uncontrolled_wording_change(self):
        self.rows[0]['wording']='Changed'; self.rows[0]['references']=[]; self.assertTrue(any('baseline change' in x for x in self.check()))
    def test_status_typo(self):
        self.rows[0]['status']='Done'; self.assertTrue(any('uncontrolled' in x for x in self.check()))
    def test_missing_field(self):
        del self.rows[0]['acceptance_criteria']; self.assertTrue(any('missing fields' in x for x in self.check()))
    def test_evidence_type(self):
        self.rows[0]['implementation']='file'; self.assertTrue(any('string lists' in x for x in self.check()))
    def test_html_escapes_content(self):
        self.rows[0]['wording']='<script>alert(1)</script>'; self.check(); render(self.root)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', (self.root/'RTM.html').read_text(encoding='utf-8'))

    def test_label_alone_cannot_authorise_change(self):
        self.rows[0]['wording']='Changed'
        self.rows[0]['references']=['CR-FAKE']
        self.assertTrue(any('approved matching CR' in x for x in self.check()))

    def test_exact_approved_change_record(self):
        self.rows[0]['wording']='Changed'
        self.rows[0]['references']=['CR-TEST']
        (self.root/'approval.txt').write_text('TEST FIXTURE approval; not actual evidence')
        changes=changes_for(self.root,self.rows)
        record={'id':'CR-TEST','status':'Approved','requirements':[self.rows[0]['id']],
                'changes':changes,'approval_evidence':'approval.txt'}
        (self.root/'change_register.json').write_text(json.dumps([record]))
        self.assertEqual(self.check(),[])
        self.rows[0]['priority']='Could Have'
        self.assertTrue(any('approved matching CR' in x for x in self.check()))

    def test_diff_retains_old_and_new_values(self):
        before=self.rows[0]['acceptance_criteria']
        self.rows[0]['acceptance_criteria']='New criterion'
        diff=changes_for(self.root,self.rows)
        self.assertEqual(diff,[{'id':self.rows[0]['id'],'field':'acceptance_criteria','before':before,'after':'New criterion'}])

    def test_manifest_detects_tampering(self):
        (self.root/'proof.txt').write_bytes(b'original')
        (self.root/'evidence_manifest.json').write_text(json.dumps([{'path':'proof.txt','sha256':hashlib.sha256(b'original').hexdigest()}]))
        self.assertEqual(verify_manifest(self.root),[])
        (self.root/'proof.txt').write_bytes(b'changed')
        self.assertTrue(verify_manifest(self.root))

if __name__=='__main__': unittest.main()
