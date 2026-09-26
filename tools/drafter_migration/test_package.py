import hashlib,json,tempfile,unittest
from pathlib import Path
from tools.drafter_migration.verify_package import verify,install

class PackageTests(unittest.TestCase):
    def fixture(self,root):
        p=root/'artifacts/data/brawl_reports/model.json';p.parent.mkdir(parents=True);p.write_bytes(b'{}')
        m={'files':[{'path':str(p.relative_to(root)),'bytes':2,'sha256':hashlib.sha256(b'{}').hexdigest()}]}
        (root/'manifest.json').write_text(json.dumps(m));return p,m
    def test_tamper_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,m=self.fixture(root);verify(root);p.write_bytes(b'[]')
            with self.assertRaises(ValueError):verify(root)
    def test_install_never_overwrites_different_artifact(self):
        with tempfile.TemporaryDirectory() as d,tempfile.TemporaryDirectory() as t:
            root=Path(d);self.fixture(root);target=Path(t)
            self.assertEqual(install(root,target),1);self.assertEqual(install(root,target),0)
            p=target/'data/brawl_reports/model.json';p.write_bytes(b'original')
            with self.assertRaises(ValueError):install(root,target)
            self.assertEqual(p.read_bytes(),b'original')
    def test_traversal_and_symlink_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,m=self.fixture(root);m['files'][0]['path']='../outside'
            (root/'manifest.json').write_text(json.dumps(m))
            with self.assertRaises(ValueError):verify(root)
            m['files'][0]['path']=str(p.relative_to(root));(root/'manifest.json').write_text(json.dumps(m))
            p.unlink();p.symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):verify(root)
