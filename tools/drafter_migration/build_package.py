"""Explicit source-only packaging; logical dump, read-only source, no API/cleanup."""
import hashlib,json,os,shutil,subprocess,tarfile
from pathlib import Path
from tools.drafter_migration.verify_package import sha

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'backups/drafter-v2-migration-20260926'
DB='drafter-v2-isolated-db-1'
SOURCE='9be54cc3b4d0f1c034d7890fa324e0418214e9ab'

def run(args,**kwargs):return subprocess.check_output(args,**kwargs)
def sql(statement):
    return run(['docker','exec','-e','PGOPTIONS=-c default_transaction_read_only=on',DB,
        'psql','-X','-U','postgres','-d','postgres','-Atc',statement],text=True).strip()

def main():
    os.umask(0o077)
    if (OUT/'manifest.json').exists():raise ValueError('Preserve existing package')
    if run(['git','status','--porcelain'],cwd=ROOT):raise ValueError('Commit reviewed code/docs before packaging')
    mounts=json.loads(run(['docker','inspect',DB,'--format','{{json .Mounts}}']))
    assert len(mounts)==1 and mounts[0]['Source']==str(ROOT/'data/db') and mounts[0]['Destination']=='/var/lib/postgresql/data'
    assert sql("SELECT count(*) FROM pg_largeobject_metadata")=='0','Unclassified large objects'
    assert sql("SELECT count(*) FROM pg_namespace WHERE nspname NOT LIKE 'pg_%' AND nspname NOT IN ('public','information_schema')")=='0'
    assert sql("SELECT count(*) FROM drafter_collectorrun WHERE status='running'")=='0'
    baseline=json.loads((OUT/'source-audit.json').read_text())
    # Hold the existing shared collector lock during dump. No database row writes.
    lock=subprocess.Popen(['docker','exec','-i',DB,'psql','-X','-qAt','-U','postgres','-d','postgres'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    try:
        lock.stdin.write('SELECT pg_try_advisory_lock(20260923,1201);\n');lock.stdin.flush()
        if lock.stdout.readline().strip()!='t':raise ValueError('Collector lock is occupied')
        args=['docker','exec','-e','PGOPTIONS=-c default_transaction_read_only=on',DB,'pg_dump','-U','postgres','-d','postgres','--format=custom','--no-owner','--no-privileges','--schema=public']
        args+=['--exclude-table-data=public.'+n for n in baseline['excluded_table_data']]
        with (OUT/'database.dump').open('xb') as stream:subprocess.run(args,stdout=stream,check=True)
    finally:
        lock.stdin.close();lock.wait(timeout=30)
    with (OUT/'database.dump').open('rb') as stream:
        toc=run(['docker','exec','-i',DB,'pg_restore','--list'],stdin=stream).decode()
    for n in baseline['excluded_table_data']:
        assert 'TABLE DATA public '+n+' ' not in toc,'Unexpected non-Drafter data in dump'
    for n in baseline['source_table_counts']:
        if n.startswith('drafter_'):assert 'TABLE DATA public '+n+' ' in toc
    (OUT/'database.toc').write_text(toc)
    subprocess.run(['docker','run','--rm','--read-only','--network','drafter-v2-isolated_backend',
        '--mount',f'type=bind,src={ROOT},dst=/code,readonly','--mount',f'type=bind,src={OUT},dst=/handoff',
        '-e','POSTGRES_NAME=postgres','-e','POSTGRES_USER=postgres','-e','POSTGRES_PASSWORD=postgres',
        '-e','PGOPTIONS=-c default_transaction_read_only=on','-e','PYTHONDONTWRITEBYTECODE=1',
        '-e','DRAFTER_MIGRATION_EXPECTED=/handoff/source-audit.json','-e','DRAFTER_MIGRATION_SOURCE_RECHECK=1',
        '-e','DRAFTER_MIGRATION_OUTPUT=/handoff/source-audit-recheck.json','--entrypoint','python','django-dev',
        'manage.py','shell','-c',"exec(open('tools/drafter_migration/audit.py').read())"],check=True)
    inventory_script="""import hashlib,json,pathlib
root=pathlib.Path('/reports');rows=[]
for p in sorted(root.iterdir()):
 if not p.is_file() or p.is_symlink():raise ValueError('Unexpected source artifact')
 if p.name not in {
 'development-20260925-001.json','development-20260925-002-1k.json','development-20260925-003-batch01.json',
 'development-20260925-004-batch02.json','development-20260925-005-5k.json','development-20260925-006-10k.json',
 'development-20260925-007-session-checkpoint.json','development-experiment-001-result.json',
 'legacy-bundle-replay.json.gz','legacy-bundle-verified-a.json.gz','legacy-bundle-verified-b.json.gz',
 'legacy-evaluation-23069ec9ec9cbbc8b7475e590c18e9548c4666395834886e12c0cd8436830527.json.gz',
 'legacy-input-final.json.gz','legacy-input-v1.json.gz','v2_challenger.json','v2_opponent_experiment.json'}:raise ValueError('Unclassified artifact')
 h=hashlib.sha256(p.read_bytes()).hexdigest()
 rows.append({'path':'data/brawl_reports/'+p.name,'bytes':p.stat().st_size,'sha256':h})
print(json.dumps(rows))"""
    inventory=json.loads(run(['docker','run','--rm','--read-only','--network','none','--mount',f'type=bind,src={ROOT}/data/brawl_reports,dst=/reports,readonly','--entrypoint','python','django-dev','-c',inventory_script]))
    for row in inventory:
        name=Path(row['path']).name
        duplicate=name in ('legacy-bundle-verified-a.json.gz','legacy-bundle-verified-b.json.gz')
        row.update(required=not duplicate and name!='legacy-input-v1.json.gz',included=not duplicate,
            purpose=('redundant independent D-022 build; identical primary bundle retained' if duplicate else
                'historical pre-verification Legacy input' if name=='legacy-input-v1.json.gz' else
                'immutable development membership/provenance or candidate archive' if name.startswith('development-') else
                'frozen Legacy input/bundle/verification receipt' if name.startswith('legacy-') else
                'working V2 / preserved negative opponent experiment'))
    selected=[r for r in inventory if r['included']]
    primary=next(r for r in inventory if Path(r['path']).name.startswith('legacy-evaluation-'))
    for r in inventory:
        if not r['included']:assert r['sha256']==primary['sha256']
    with (OUT/'artifact-transfer.tar').open('xb') as stream:
        subprocess.run(['docker','run','--rm','--read-only','--network','none','--mount',f'type=bind,src={ROOT}/data/brawl_reports,dst=/source/data/brawl_reports,readonly','--entrypoint','tar','django-dev','-C','/source','-cf','-']+[r['path'] for r in selected],stdout=stream,check=True)
    with tarfile.open(OUT/'artifact-transfer.tar') as archive:
        names={r['path'] for r in selected}
        for item in archive:
            if item.name not in names or not item.isfile():raise ValueError('Unexpected archive entry')
            dest=OUT/'artifacts'/item.name;dest.parent.mkdir(parents=True,exist_ok=True)
            with archive.extractfile(item) as src,dest.open('xb') as dst:shutil.copyfileobj(src,dst)
    # Remove only our intermediate transport tar, never source data.
    (OUT/'artifact-transfer.tar').unlink()
    for row in selected:assert sha(OUT/'artifacts'/row['path'])==row['sha256']
    revision=run(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    (OUT/'CODE_REVISION').write_text(revision+'\n')
    shutil.copyfile(ROOT/'docs/drafter-v2/MIGRATION_RUNBOOK.md',OUT/'RUNBOOK.md')
    shutil.copyfile(ROOT/'tools/drafter_migration/verify_package.py',OUT/'verify_package.py')
    (OUT/'artifact-inventory.json').write_text(json.dumps(inventory,indent=2,sort_keys=True)+'\n')
    tracked=run(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    sizes={'tracked_checkout_bytes':sum((ROOT/p).stat().st_size for p in tracked if p and (ROOT/p).is_file()),
        'database_logical_dump_bytes':(OUT/'database.dump').stat().st_size,
        'source_database_allocated_bytes':int(sql('SELECT pg_database_size(current_database())')),
        'private_artifacts_required_bytes':sum(r['bytes'] for r in inventory if r['required']),
        'private_artifacts_optional_bytes':sum(r['bytes'] for r in inventory if not r['required']),
        'included_private_artifact_bytes':sum(r['bytes'] for r in selected),
        'external_raw_files_bytes':0,'raw_payloads':'2897 rows inside PostgreSQL; no external raw directory in this worktree',
        'git_objects':run(['git','count-objects','-v'],cwd=ROOT,text=True),
        'excluded':'raw PGDATA, unrelated media/data, credentials, caches, node_modules, venvs, image layers'}
    (OUT/'storage.json').write_text(json.dumps(sizes,indent=2,sort_keys=True)+'\n')
    allowed={'source-audit.json','source-audit-recheck.json','database.dump','database.toc','CODE_REVISION','RUNBOOK.md','verify_package.py','artifact-inventory.json','storage.json'} | {'artifacts/'+r['path'] for r in selected}
    assert {str(p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file()}==allowed, 'Unclassified package file'
    files=[{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
    manifest={'schema':'drafter-migration-package-1','source_state_revision':SOURCE,'restore_revision':revision,
        'source_database_container':DB,'source_database_mount':str(ROOT/'data/db'),
        'postgres_version':'16.0','database_format':'pg_dump custom; no owner/ACL; unrelated row data excluded',
        'secrets_included':False,'target_verified':False,'files':files}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    with (OUT/'SHA256SUMS').open('x') as stream:
        for p in sorted(OUT.rglob('*')):
            if p.is_file() and p.name!='SHA256SUMS':stream.write(sha(p)+'  '+str(p.relative_to(OUT))+'\n')
    print(json.dumps({'package':str(OUT),'restore_revision':revision,'storage':sizes},indent=2))

if __name__=='__main__':main()
