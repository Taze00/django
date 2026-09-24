"""Query eligibility is separate from eligible Ranked evidence (D-023)."""
from django.db import models


class DiscoveryPlayer(models.Model):
    player = models.OneToOneField("drafter.TrackedPlayer", on_delete=models.PROTECT,
                                  related_name="discovery_frontier")
    first_source = models.CharField(max_length=32)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()
    discovery_depth = models.PositiveIntegerField(default=0)
    first_run = models.ForeignKey("drafter.CollectorRun", on_delete=models.PROTECT, related_name="+")


class DiscoveryObservation(models.Model):
    # source=solo_ranked + eligible linked Match is evidence. Raw battle_type
    # or trophy discovery alone is never Ranked evidence.
    player = models.ForeignKey(DiscoveryPlayer, on_delete=models.PROTECT, related_name="observations")
    source = models.CharField(max_length=32)
    observed_at = models.DateTimeField()
    payload = models.ForeignKey("drafter.RawPayload", on_delete=models.PROTECT, related_name="discovery_observations")
    run = models.ForeignKey("drafter.CollectorRun", on_delete=models.PROTECT, related_name="discovery_observations")
    json_pointer = models.CharField(max_length=160)
    queried_player = models.ForeignKey("drafter.TrackedPlayer", on_delete=models.PROTECT, null=True, related_name="+")
    match = models.ForeignKey("drafter.Match", on_delete=models.PROTECT, null=True, related_name="+")
    battle_type = models.CharField(max_length=80, default="UNKNOWN")
    relationship = models.CharField(max_length=20, default="UNKNOWN")

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["player", "payload", "run", "source", "json_pointer"],
            name="drafter_unique_discovery_observation",
        )]
