"""D-023: authentic observed identities are queryable, not automatically evidence."""
from collections import Counter
from types import SimpleNamespace
from django.utils.dateparse import parse_datetime

from drafter.models import CollectorRun, Datenquelle, Match, RawPayload, TrackedPlayer
from drafter.models.discovery import DiscoveryPlayer, DiscoveryObservation
from drafter.services.brawl_api_client import pfad_battlelog
from drafter.services.ingest.importer import inhalts_hash
from drafter.services.ingest.parser import FORMAT_OFFIZIELLER_BATTLELOG
from drafter.services.v2_future_window import OLD_END
from drafter.services.tagged_frontier import TaggedFrontierCollector, beobachteter_tag, eligible

SAMPLING = "observed_discovery_pilot_v1"


class DiscoveryFrontierCollector(TaggedFrontierCollector):
    sampling = SAMPLING
    budget_limit = 10
    frontier_model = DiscoveryPlayer
    observation_model = DiscoveryObservation
    frontier_relation = "discovery_frontier"
    discovered_origin = "official_observed"

    def __init__(self, *, source_payloads, pilot_id, protocol_hash, **kwargs):
        super().__init__(**kwargs)
        if self.after < OLD_END:
            raise ValueError("Pilot cutoff cannot reopen historical evidence")
        if self.ranking_seeds:
            raise ValueError("This pilot makes no ranking requests")
        if not pilot_id or len(protocol_hash) != 64:
            raise ValueError("A pinned pilot identity and protocol hash are required")
        if not source_payloads or len(source_payloads) > 6:
            raise ValueError("Pin one to six existing official battlelog payloads")
        self.sources = source_payloads
        self.pilot_id = pilot_id
        self.protocol_hash = protocol_hash
        self.raw_types = Counter()
        self.bootstrap_types = Counter()
        self.seen_response_tags = set()
        self.bootstrap_tags = set()

    def _execute(self):
        # Inside the parent's shared advisory lock; crashes consume this pilot too.
        if CollectorRun.objects.filter(parameters__pilot_id=self.pilot_id).exists():
            raise ValueError("Pilot already attempted; immediate retries are forbidden")
        return super()._execute()

    def _prepare_frontier(self):
        self.run.parameters.update(pilot_id=self.pilot_id, protocol_hash=self.protocol_hash,
            purpose="pre_registration_development_pilot", future_test_eligible=False,
            source_payloads=self.sources)
        self.run.save(update_fields=["parameters"])
        payloads = [RawPayload.objects.get(pk=s["id"], content_hash=s["content_hash"]) for s in self.sources]
        for payload in payloads:
            self._validate_payload(payload)
        for payload in payloads:
            # Request identity is graph-edge metadata, not an admission by itself.
            tracked = TrackedPlayer.objects.get(tag=payload.reference)
            parent = SimpleNamespace(player=tracked, player_id=tracked.pk, discovery_depth=0)
            self.depths[tracked.pk] = 0
            self._discover(payload, parent, bootstrap=True)
        self.metrics["bootstrap_unique_observed_tags"] = len(self.bootstrap_tags)
        self.metrics["query_eligible_tags_available"] = DiscoveryPlayer.objects.count()
        self.metrics["query_eligible_tags_due"] = self._due().filter(discovery_frontier__isnull=False).count()

    def _validate_payload(self, payload):
        envelope = payload.payload
        if (payload.source != Datenquelle.API or payload.format != FORMAT_OFFIZIELLER_BATTLELOG
                or not payload.collector_run_id or payload.fetched_at is None
                or payload.collector_run.parameters.get("strategie") not in ("tagged_frontier_v1", SAMPLING)
                or payload.sampling != payload.collector_run.parameters.get("strategie")
                or not isinstance(envelope, dict)
                or inhalts_hash(envelope) != payload.content_hash
                or envelope.get("herkunft") != "api-mitschnitt"
                or envelope.get("http_status") != 200
                or envelope.get("referenz") != payload.reference
                or not beobachteter_tag(payload.reference)
                or envelope.get("endpoint") != "/" + pfad_battlelog(payload.reference).lstrip("/")
                or parse_datetime(envelope.get("abgerufen_am", "")) != payload.fetched_at):
            raise ValueError("Unverified official battlelog provenance; discovery refused")

    def _discover(self, payload, parent, *, bootstrap=False):
        self._validate_payload(payload)
        answer = payload.payload.get("antwort")
        items = answer.get("items") if isinstance(answer, dict) else None
        if not isinstance(items, list):
            return
        for index, item in enumerate(items):
            battle = item.get("battle") if isinstance(item, dict) else None
            if not isinstance(battle, dict):
                continue
            raw_type = battle.get("type")
            battle_type = raw_type if isinstance(raw_type, str) and len(raw_type) <= 80 else "UNKNOWN"
            (self.bootstrap_types if bootstrap else self.raw_types)[battle_type] += 1
            source = {"ranked": "trophy_battlelog", "soloRanked": "soloRanked_battlelog"}.get(
                battle_type, "other_battlelog")
            teams = battle.get("teams")
            if not isinstance(teams, list):
                continue  # No inference from names, IDs or missing team structures.
            own_sides = [i for i, team in enumerate(teams) if isinstance(team, list)
                         and any(isinstance(p, dict) and beobachteter_tag(p.get("tag")) == parent.player.tag
                                 for p in team)]
            for ti, team in enumerate(teams):
                if not isinstance(team, list):
                    continue
                for pi, observed in enumerate(team):
                    tag = beobachteter_tag(observed.get("tag")) if isinstance(observed, dict) else None
                    if tag is None:
                        self.metrics["invalid_discovered_tags"] += 1
                        continue
                    (self.bootstrap_tags if bootstrap else self.seen_response_tags).add(tag)
                    relationship = "UNKNOWN"
                    if len(own_sides) == 1:
                        relationship = ("self" if tag == parent.player.tag else
                                        "teammate" if ti == own_sides[0] else "opponent")
                    pointer = f"/antwort/items/{index}/battle/teams/{ti}/{pi}/tag"
                    frontier, new = self._observe(tag, source, payload, pointer, parent=parent)
                    DiscoveryObservation.objects.filter(player=frontier, source=source,
                        payload=payload, run=self.run, json_pointer=pointer).update(
                            battle_type=battle_type, relationship=relationship)
                    self.metrics["new_discovered_tags"] += int(new)
                    self.summary.spieler_entdeckt += int(new)

    def _battlelog(self, player, answer):
        super()._battlelog(player, answer)
        payload = RawPayload.objects.get(collector_run=self.run, reference=player.tag,
                                        format=FORMAT_OFFIZIELLER_BATTLELOG)
        parent = DiscoveryPlayer.objects.select_related("player").get(player=player)
        self._discover(payload, parent)

    def _extra_report(self):
        evidence = DiscoveryObservation.objects.filter(source="solo_ranked", match__isnull=False)
        match_ids = set(evidence.values_list("match_id", flat=True))
        valid = {m.pk for m in Match.objects.filter(pk__in=match_ids).prefetch_related("players") if eligible(m)}
        return {
            "purpose": "pre_registration_development_pilot", "future_test_eligible": False,
            "raw_battle_types": dict(self.raw_types), "bootstrap_raw_battle_types": dict(self.bootstrap_types),
            "unique_response_player_tags": len(self.seen_response_tags),
            "unique_response_tags_not_in_bootstrap": len(self.seen_response_tags - self.bootstrap_tags),
            "discovery_frontier_size": DiscoveryPlayer.objects.count(),
            "ranked_evidence_frontier_size": evidence.filter(match_id__in=valid).values("player_id").distinct().count(),
            "ranked_evidence_matches": len(valid),
        }
