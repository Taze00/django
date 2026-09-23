"""Offline D-010 claim archive. No current-state, feature or historical lookup.

The reviewed annotation digest is a deliberately closed allowlist. Adding another
revision requires evidence review and a code change, never just a new timestamp.
The publisher response digest is provenance, not proof that its body is present.
"""
import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

REVIEWED_SHA256 = '8fdd66fc9763ca79b5130544ba6f17fa129d0f260445d8b4f8cfb7ef6455ac26'
MAX_BYTES = 64 * 1024


def read_reviewed(path):
    """Verify exact reviewed bytes before parsing; changed evidence fails closed."""
    with Path(path).open('rb') as stream:
        body = stream.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES or hashlib.sha256(body).hexdigest() != REVIEWED_SHA256:
        raise ValueError('Unreviewed or corrupt claim artifact; quarantine for review')
    return body


def archive(source, directory):
    """Atomically install exact annotation bytes without replacing any record.

    A matching existing record is idempotent; corruption is never repaired by
    overwrite. The archive stores annotations, not the original publisher body.
    """
    body = read_reviewed(source)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / (REVIEWED_SHA256 + '.json')
    fd, temporary = tempfile.mkstemp(prefix='.claim-', dir=directory)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError:
            read_reviewed(destination)
    finally:
        os.unlink(temporary)
    return destination


def explanations(path, *, purpose='archived_source_explanation'):
    """Report the dated source statement, never assert an equipped/active effect.

    There is intentionally no current-time, match-time, loadout inference or
    numeric feature API. Null validity remains unknown, not an open interval.
    """
    if purpose != 'archived_source_explanation':
        raise ValueError('Current reuse needs revalidation; numeric/historical use is forbidden')
    document = json.loads(read_reviewed(path))
    result = []
    for claim in document['claims']:
        unit = '' if claim['unit'] is None else ' ' + claim['unit']
        result.append({
            'claim': claim,
            'annotation_sha256': REVIEWED_SHA256,
            'status': 'ARCHIVED_SOURCE_STATEMENT',
            'current_validity': 'UNKNOWN',
            'source_body_availability': 'NOT_CHECKED',
            'text': (
                f"Source observed at {claim['observed_at']}: {claim['subject']} — "
                f"{claim['property']}: {claim['value']}{unit}. "
                f"Conditional on: {'; '.join(claim['requirements'])}. "
                f"Limitations: {'; '.join(claim['limitations'])}. "
                'Equipped loadout and active effect: UNKNOWN. '
                'Effective validity boundaries: UNKNOWN. '
                'Present-day applicability: UNKNOWN; source revalidation required. '
                f"Source: {claim['source_url']} ({claim['source_section']}); "
                f"publisher snapshot SHA-256: {claim['source_sha256']}."
            ),
        })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--claims', required=True, type=Path)
    parser.add_argument('--archive-dir', type=Path,
                        help='Optional append-only annotation archive; no publisher body is stored')
    args = parser.parse_args()
    try:
        path = archive(args.claims, args.archive_dir) if args.archive_dir else args.claims
        result = explanations(path)
    except (ValueError, OSError) as error:
        parser.exit(2, f'{error}\n')
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
