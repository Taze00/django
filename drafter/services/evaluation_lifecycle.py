"""Append-only lifecycle decisions supersede, never rewrite, registrations."""
import json
from pathlib import Path

ABORT_FILE = Path(__file__).resolve().parents[2] / 'docs/drafter-v2/PROSPECTIVE_ABORT_FOR_DEVELOPMENT.json'


def aborted_protocols():
    if not ABORT_FILE.exists():
        return set()
    receipt = json.loads(ABORT_FILE.read_text())
    if receipt['status'] != 'ABORTED_FOR_DEVELOPMENT_BEFORE_EVALUATION':
        raise ValueError('Unknown evaluation lifecycle decision; fail closed')
    return {receipt['protocol_sha256']}


def ensure_evaluation_active(protocol):
    from drafter.services.v2_future_window import digest
    if digest(protocol) in aborted_protocols():
        raise ValueError('ABORTED_FOR_DEVELOPMENT_BEFORE_EVALUATION: no prospective collection, sealing or evaluation')


def development_origin(origin):
    return (origin.get('sampling') in ('observed_discovery_pilot_v1', 'ranked_development_v1')
            or origin.get('protocol_sha256') in aborted_protocols())
