"""Run-6 audit, no historical examples, tags or response bodies."""
import json
from drafter.models import CollectorRun, RawPayload, Match
from drafter.services.tagged_frontier import eligible
run=CollectorRun.objects.get(pk=6)
raw=RawPayload.objects.filter(collector_run=run)
matches=Match.objects.filter(payloads__in=raw).distinct().prefetch_related('players')
print(json.dumps({'run_id':run.pk,'started_at':run.started_at.isoformat(),
 'finished_at':run.finished_at.isoformat() if run.finished_at else None,
 'status':run.status,'parameters':run.parameters,'report':run.report,
 'payloads':list(raw.order_by('id').values('id','content_hash','format','sampling','parse_status')),
 'linked_matches':matches.count(),'eligible_soloRanked':sum(eligible(m) for m in matches)},sort_keys=True,indent=2))
