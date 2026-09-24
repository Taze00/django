"""Publish D-024 once after the implementation commit; no DB/API/model execution."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from drafter.services.v2_future_window import ACQUISITION, digest, publish, register, validate

root = Path('docs/drafter-v2')
if subprocess.check_output(['git','status','--porcelain']).strip():
    raise SystemExit('Commit implementation/preflight before registration')
revision = subprocess.check_output(['git','rev-parse','HEAD']).decode().strip()
preflight = json.loads((root/'PROSPECTIVE_PREFLIGHT.json').read_text())
pilot_path = root/'DISCOVERY_PILOT_RESULT.json'
pilot = json.loads(pilot_path.read_text())
assert pilot['linked_eligible_soloRanked'] == pilot['report']['new_eligible_solo_ranked_matches'] > 0
assert preflight['pilot_common_eligible'] > 0
pilot_hash = hashlib.sha256(pilot_path.read_bytes()).hexdigest()
assert pilot_hash == preflight['development']['pilot_result_file_sha256']
assert preflight['development_sha256'] == digest(preflight['development'])
files = set(Path('drafter/services').rglob('*.py')) | set(Path('drafter/models').rglob('*.py'))
files.update(Path(f) for f in ('drafter/config.py','drafter/attributes.py',
    'drafter/management/commands/collect_prospective_frontier.py',
    'drafter/management/commands/drafter_v2_future_window.py',
    'docs/drafter-v2/register_prospective_window.py'))
artifacts = json.loads((root/'LEGACY_BUNDLE_ARTIFACTS.json').read_text())['artifacts']
legacy = next(a for a in artifacts if '/legacy-evaluation-' in a['path'])
assert hashlib.sha256(Path(legacy['path']).read_bytes()).hexdigest() == legacy['file_sha256']
v2_hash = hashlib.sha256(Path('data/brawl_reports/v2_challenger.json').read_bytes()).hexdigest()
assert v2_hash == '92e0b427bf9abce62e047419ea1008f740c9ee7b39b1458ae15692402b7cf52d'
acquisition = {'policy':ACQUISITION.copy(), 'pilot_result_sha256':pilot_hash,
    'pilot_new_eligible':pilot['report']['new_eligible_solo_ranked_matches'],
    'pilot_finished_at':pilot['finished_at'], 'legacy_artifact':legacy,
    'implementation_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
now = datetime.now(timezone.utc)
protocol = register(now=now, development_end=pilot['finished_at'],
    start='2026-09-25T00:00:00Z', end='2026-10-09T00:00:00Z',
    v2_hash=v2_hash, legacy_hash=legacy['content_sha256'],
    development_hash=preflight['development_sha256'], revision=revision,
    legacy_verification=json.loads((root/'LEGACY_BUNDLE_VERIFICATION.json').read_text()),
    acquisition=acquisition, common_context=preflight['common_context'])
validate(protocol)
receipt={'status':'REGISTERED_NOT_STARTED_NOT_EVALUATED',
    'protocol_sha256':digest(protocol), 'registered_at':protocol['registered_at'],
    'start_exclusive':protocol['start_exclusive'], 'end_inclusive':protocol['end_inclusive'],
    'implementation_revision':revision, 'old_holdout':'permanently_closed',
    'pilot_excluded':True, 'recurring_collector':False}
for name in ('PROSPECTIVE_WINDOW.json','PROSPECTIVE_REGISTRATION.json'):
    if (root/name).exists():
        raise SystemExit('Registration already exists; never replace it')
publish(root/'PROSPECTIVE_WINDOW.json', protocol)
publish(root/'PROSPECTIVE_REGISTRATION.json', receipt)
print(json.dumps(receipt, indent=2, sort_keys=True))
