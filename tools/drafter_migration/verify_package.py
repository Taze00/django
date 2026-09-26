"""Verify a private package; optionally install artifacts without overwriting files."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def checked_path(root,name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe manifest path')
    result=root/p
    if result.is_symlink() or not result.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe package link')
    return result


def verify(root):
    manifest=json.loads((root/'manifest.json').read_text())
    for row in manifest['files']:
        p=checked_path(root,row['path'])
        if not p.is_file() or p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:
            raise ValueError('Integrity mismatch: '+row['path'])
    return manifest


def install(root,target):
    manifest=verify(root)
    jobs=[]
    for row in manifest['files']:
        if not row['path'].startswith('artifacts/data/brawl_reports/'):continue
        dest=checked_path(target,row['path'].removeprefix('artifacts/'))
        if dest.exists():
            if sha(dest)!=row['sha256']:raise ValueError('Refuse existing different artifact: '+str(dest))
        else:jobs.append((root/row['path'],dest))
    for source,dest in jobs:
        dest.parent.mkdir(parents=True,exist_ok=True)
        with source.open('rb') as src,dest.open('xb') as dst:shutil.copyfileobj(src,dst)
    return len(jobs)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('package',type=Path);parser.add_argument('--install-artifacts',type=Path)
    args=parser.parse_args();m=verify(args.package)
    if args.install_artifacts:print('Installed',install(args.package,args.install_artifacts),'artifacts')
    print('PASS:',len(m['files']),'files; restore revision',m['restore_revision'])
