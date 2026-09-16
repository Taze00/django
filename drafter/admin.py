"""Django-Admin des Drafters.

Zweck: die Demo-Daten sollen ohne Code-Aenderung pflegbar sein. Wer
findet, dass Gale zu stark gegen Bull eingeschaetzt ist, aendert das
hier - nicht in seed_data.py.

Eine Warnung dazu: `seed_brawl_data` gleicht die Demo-Daten wieder an
die Datei an. Wer Aenderungen behalten will, stellt `source` auf
"Manuell gepflegt" - dann fasst `--reset` sie nicht an.
"""

from django.contrib import admin
from django.utils.html import format_html

from drafter.models import (
    CollectorRun, TrackedPlayer,
    Brawler, BrawlerBalanceChange, BrawlerItem, BrawlerStat, BrawlMap, BuildStat,
    BuildRule, CounterStat, Datenquelle, GameMode, Patch, SynergyStat,
    UserBrawlerPreference,
)


def _farbpunkt(objekt):
    return format_html(
        '<span style="display:inline-block;width:12px;height:12px;'
        'border-radius:3px;background:{}"></span>',
        objekt.color,
    )


class QuelleFilter(admin.SimpleListFilter):
    """Demo von echt trennen - die wichtigste Unterscheidung im Bestand."""

    title = "Datenquelle"
    parameter_name = "quelle"

    def lookups(self, request, model_admin):
        return Datenquelle.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(source=self.value())
        return queryset


@admin.register(Brawler)
class BrawlerAdmin(admin.ModelAdmin):
    list_display = ("farbe_punkt", "name", "role", "tags", "quelle", "is_active")
    list_display_links = ("name",)
    list_filter = ("role", "is_active", QuelleFilter)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("name", "slug", "role", "tags", "is_active")}),
        ("Darstellung", {"fields": ("image_url", "color")}),
        ("Eigenschaften", {
            "fields": ("attributes", "draft_values"),
            "description": (
                "Schlüssel müssen aus drafter/attributes.py stammen, Werte 0-100. "
                "Unbekannte Schlüssel werden beim Speichern abgelehnt."
            ),
        }),
        ("Herkunft", {"fields": ("source", "notes")}),
    )

    @admin.display(description="")
    def farbe_punkt(self, objekt):
        return _farbpunkt(objekt)

    @admin.display(description="Quelle", ordering="source")
    def quelle(self, objekt):
        return objekt.get_source_display()


class MapInline(admin.TabularInline):
    model = BrawlMap
    extra = 0
    fields = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    show_change_link = True


@admin.register(GameMode)
class GameModeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "anzahl_maps", "is_active", "order")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MapInline]

    @admin.display(description="Maps")
    def anzahl_maps(self, objekt):
        return objekt.maps.count()


@admin.register(BrawlMap)
class BrawlMapAdmin(admin.ModelAdmin):
    list_display = ("name", "game_mode", "hauptanforderungen", "is_active")
    list_filter = ("game_mode", "is_active", QuelleFilter)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Praegend")
    def hauptanforderungen(self, objekt):
        return ", ".join(e.label for e in objekt.wichtigste_anforderungen(3))


@admin.register(Patch)
class PatchAdmin(admin.ModelAdmin):
    list_display = ("name", "released_on", "is_current", "anzahl_aenderungen")
    list_filter = ("is_current",)
    date_hierarchy = "released_on"

    @admin.display(description="Aenderungen")
    def anzahl_aenderungen(self, objekt):
        return objekt.changes.count()


@admin.register(BrawlerBalanceChange)
class BalanceChangeAdmin(admin.ModelAdmin):
    list_display = ("brawler", "patch", "severity", "direction", "is_rework")
    list_filter = ("severity", "direction", "is_rework", "patch")
    search_fields = ("brawler__name",)
    autocomplete_fields = ("brawler",)


@admin.register(BrawlerStat)
class BrawlerStatAdmin(admin.ModelAdmin):
    list_display = (
        "brawler", "kontext", "window_label", "adjusted_rate", "raw_rate",
        "games", "sample_size", "confidence", "quelle",
    )
    list_filter = ("rank_pool", "window_label", "game_mode", "patch", QuelleFilter)
    search_fields = ("brawler__name",)
    autocomplete_fields = ("brawler",)
    readonly_fields = ("context_key", "created_at", "updated_at")

    @admin.display(description="Kontext")
    def kontext(self, objekt):
        return objekt.brawl_map or objekt.game_mode or "allgemein"

    @admin.display(description="Quelle")
    def quelle(self, objekt):
        return objekt.get_source_display()


@admin.register(CounterStat)
class CounterStatAdmin(admin.ModelAdmin):
    list_display = ("brawler", "enemy", "advantage", "games", "confidence", "reason", "quelle")
    list_filter = ("rank_pool", "game_mode", QuelleFilter)
    search_fields = ("brawler__name", "enemy__name", "reason")
    autocomplete_fields = ("brawler", "enemy")
    readonly_fields = ("context_key",)

    @admin.display(description="Quelle")
    def quelle(self, objekt):
        return objekt.get_source_display()


@admin.register(SynergyStat)
class SynergyStatAdmin(admin.ModelAdmin):
    list_display = ("brawler_a", "brawler_b", "synergy", "games", "confidence", "reason", "quelle")
    list_filter = ("rank_pool", "game_mode", QuelleFilter)
    search_fields = ("brawler_a__name", "brawler_b__name", "reason")
    autocomplete_fields = ("brawler_a", "brawler_b")
    readonly_fields = ("context_key",)

    @admin.display(description="Quelle")
    def quelle(self, objekt):
        return objekt.get_source_display()


@admin.register(BuildStat)
class BuildStatAdmin(admin.ModelAdmin):
    list_display = (
        "brawler", "item_kind", "item_slug", "advantage", "adjusted_rate",
        "games", "sample_size", "confidence", "window_label", "quelle",
    )
    list_filter = ("item_kind", "rank_pool", "window_label", QuelleFilter)
    search_fields = ("brawler__name", "item_slug")
    autocomplete_fields = ("brawler", "item")
    readonly_fields = ("context_key",)

    @admin.display(description="Quelle")
    def quelle(self, objekt):
        return objekt.get_source_display()


class BuildRuleInline(admin.TabularInline):
    model = BuildRule
    extra = 0
    fields = ("condition", "weight", "reason_template", "priority", "is_active")


@admin.register(BrawlerItem)
class BrawlerItemAdmin(admin.ModelAdmin):
    list_display = ("name", "brawler", "kind", "base_weight", "anzahl_regeln", "is_active")
    list_filter = ("kind", "is_active", QuelleFilter)
    search_fields = ("name", "brawler__name")
    autocomplete_fields = ("brawler",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BuildRuleInline]

    @admin.display(description="Regeln")
    def anzahl_regeln(self, objekt):
        return objekt.rules.count()


@admin.register(BuildRule)
class BuildRuleAdmin(admin.ModelAdmin):
    list_display = ("item", "kurzbegruendung", "weight", "priority", "is_active")
    list_filter = ("is_active", "item__kind")
    search_fields = ("item__name", "reason_template")
    autocomplete_fields = ("item",)

    @admin.display(description="Begruendung")
    def kurzbegruendung(self, objekt):
        return objekt.reason_template[:70]


@admin.register(UserBrawlerPreference)
class UserBrawlerPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "brawler", "confidence", "favorite", "avoid", "updated_at")
    list_filter = ("favorite", "avoid")
    search_fields = ("user__username", "brawler__name")
    autocomplete_fields = ("brawler",)


# --- Rohdaten ---------------------------------------------------------------
# Nur zum Ansehen und fuer Konflikte. Rohdaten entstehen ausschliesslich
# ueber den Import - eine von Hand angelegte Partie haette keine
# Lieferung, aus der sie stammt, und waere nicht nachvollziehbar.

from drafter.models.matches import Match, MatchBan, MatchPlayer, RawPayload  # noqa: E402


class MatchPlayerInline(admin.TabularInline):
    model = MatchPlayer
    extra = 0
    can_delete = False
    fields = ("side", "brawler_name", "brawler", "player_tag", "pick_order", "build")
    readonly_fields = fields


class MatchBanInline(admin.TabularInline):
    model = MatchBan
    extra = 0
    can_delete = False
    fields = ("side", "brawler_name", "brawler", "order")
    readonly_fields = fields


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "played_at", "mode_name", "map_name", "source", "rank_pool",
        "winner_side", "has_conflict", "gesehen",
    )
    list_filter = ("source", "rank_pool", "has_conflict", "is_ranked", "game_mode")
    search_fields = ("map_name", "mode_name", "fingerprint", "external_id", "players__brawler_name")
    date_hierarchy = "played_at"
    inlines = [MatchPlayerInline, MatchBanInline]
    readonly_fields = (
        "fingerprint", "external_id", "source", "played_at", "game_mode", "brawl_map",
        "mode_name", "map_name", "patch", "rank_pool", "is_ranked", "winner_side",
        "first_pick_side", "duration_seconds", "payloads",
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="Gesehen")
    def gesehen(self, objekt):
        return objekt.gesehen


@admin.register(RawPayload)
class RawPayloadAdmin(admin.ModelAdmin):
    list_display = (
        "fetched_at", "reference", "format", "source", "parse_status",
        "match_count", "new_match_count",
    )
    list_filter = ("source", "format", "parse_status")
    search_fields = ("reference", "content_hash")
    readonly_fields = (
        "source", "format", "reference", "content_hash", "payload", "fetched_at",
        "parse_status", "parse_message", "match_count", "new_match_count",
    )

    def has_add_permission(self, request):
        return False


admin.site.site_header = "alex.volkmann.com"


@admin.register(TrackedPlayer)
class TrackedPlayerAdmin(admin.ModelAdmin):
    list_display = (
        "tag", "origin", "depth", "ranking_position", "last_fetched_at",
        "last_status", "fetch_count", "error_streak", "last_solo_ranked_count",
    )
    list_filter = ("origin", "depth", "last_status", "is_active")
    search_fields = ("tag", "discovered_from")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CollectorRun)
class CollectorRunAdmin(admin.ModelAdmin):
    list_display = ("started_at", "finished_at", "status", "abort_reason")
    list_filter = ("status",)
    # Ein Lauf ist ein Protokoll - nichts davon wird von Hand geaendert.
    readonly_fields = (
        "started_at", "finished_at", "status", "abort_reason", "parameters", "report",
    )
