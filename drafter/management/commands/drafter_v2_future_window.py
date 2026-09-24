"""Read-only future admission inventory; no outcomes returned or model executed."""
import json
from collections import Counter
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Prefetch
from drafter.models import RawPayload
from django.utils import timezone
from drafter.models import Match
from drafter.services.v2_future_window import validate, timestamp, seal, publish, digest, verify_membership


def inventory(protocol):
    # A time predicate is applied before loading any Match/players/payloads.
    rows = Match.objects.filter(played_at__gt=timestamp(protocol['start_exclusive']),
                                played_at__lte=timestamp(protocol['end_inclusive']))
    for match in rows.prefetch_related('players', Prefetch('payloads', queryset=RawPayload.objects.only(
            'source','sampling','format','collector_run_id','content_hash','fetched_at').select_related('collector_run'))).order_by('played_at','fingerprint'):
        players = list(match.players.all())
        content_sha256 = digest({'winner_side': match.winner_side, 'map': match.brawl_map_id,
                                 'mode': match.game_mode_id, 'patch': match.patch_id,
                                 'players': sorted(((p.side, p.brawler_id) for p in players), key=lambda pair: (pair[0], str(pair[1])))})
        yield {'content_sha256': content_sha256, 'fingerprint': match.fingerprint, 'reconstructed_fingerprint': match.reconstructed_fingerprint,
               'map_id': match.brawl_map_id, 'mode_id': match.game_mode_id, 'patch_id': match.patch_id,
               'brawler_ids': sorted([p.brawler_id for p in players if p.brawler_id is not None]),
               'played_at': match.played_at.isoformat(), 'source': match.source,
               'battle_type': match.battle_type, 'is_ranked': match.is_ranked,
               'has_conflict': match.has_conflict, 'result_known': match.winner_side in ('a','b'),
               'known_context': match.game_mode_id is not None and match.brawl_map_id is not None,
               'complete_unique_3v3': len(players) == 6 and Counter(p.side for p in players) == {'a':3,'b':3}
                    and all(p.brawler_id is not None for p in players) and len({p.brawler_id for p in players}) == 6,
               'origins': sorted([{'source': p.source, 'sampling': p.sampling, 'format': p.format,
                                  'run_id': p.collector_run_id, 'content_hash': p.content_hash,
                                  'protocol_sha256': p.collector_run.parameters.get('protocol_sha256') if p.collector_run_id else None,
                                  'purpose': p.collector_run.parameters.get('purpose') if p.collector_run_id else None,
                                  'code_revision': p.collector_run.parameters.get('code_revision') if p.collector_run_id else None,
                                  'fetched_at': p.fetched_at.isoformat()} for p in match.payloads.all()],
                                 key=lambda p: p['content_hash'])}


class Command(BaseCommand):
    help = 'Inventory a preregistered future window, optionally create immutable membership after close'

    def add_arguments(self, parser):
        parser.add_argument('--protocol', required=True)
        parser.add_argument('--expected-protocol-sha256', required=True, help='Digest pinned at preregistration')
        parser.add_argument('--verify-membership', help='Verify existing seal without evaluation or resealing')
        parser.add_argument('--seal-output', help='New file only; never overwrites')

    def handle(self, *args, **options):
        try:
            protocol = json.loads(Path(options['protocol']).read_text())
            validate(protocol)
            if digest(protocol) != options['expected_protocol_sha256']:
                raise ValueError('Preregistered protocol digest mismatch')
            # Stable membership/provenance snapshot; never writes the source DB.
            from django.db import connection
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
                from drafter.services.prospective_acquisition import verify_catalog
                verify_catalog(protocol)
                rows = list(inventory(protocol))
            if options['verify_membership'] and options['seal_output']:
                raise ValueError('Cannot verify and reseal together')
            if options['verify_membership']:
                result = verify_membership(protocol, json.loads(Path(options['verify_membership']).read_text()), rows)
            elif options['seal_output']:
                result = seal(protocol, rows, timezone.now())
                publish(options['seal_output'], result)
                result = {k: v for k,v in result.items() if k != 'members'}
            else:
                result = {'status': 'INVENTORY_ONLY_NOT_EVALUATED', 'n_observed': len(rows),
                          'types': dict(Counter(r['battle_type'] for r in rows)), 'protocol_sha256': digest(protocol)}
            self.stdout.write(json.dumps(result, sort_keys=True, indent=2))
        except (ValueError, TypeError, KeyError, OSError) as error:
            raise CommandError(str(error)) from error
