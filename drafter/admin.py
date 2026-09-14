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
    Brawler, BrawlerBalanceChange, BrawlerItem, BrawlerStat, BrawlMap,
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
    list_display = ("brawler", "kontext", "win_rate", "games", "confidence", "quelle")
    list_filter = ("rank_pool", "game_mode", "patch", QuelleFilter)
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
    list_display = ("brawler", "enemy", "advantage", "reason", "quelle")
    list_filter = ("rank_pool", "game_mode", QuelleFilter)
    search_fields = ("brawler__name", "enemy__name", "reason")
    autocomplete_fields = ("brawler", "enemy")
    readonly_fields = ("context_key",)

    @admin.display(description="Quelle")
    def quelle(self, objekt):
        return objekt.get_source_display()


@admin.register(SynergyStat)
class SynergyStatAdmin(admin.ModelAdmin):
    list_display = ("brawler_a", "brawler_b", "synergy", "reason", "quelle")
    list_filter = ("rank_pool", "game_mode", QuelleFilter)
    search_fields = ("brawler_a__name", "brawler_b__name", "reason")
    autocomplete_fields = ("brawler_a", "brawler_b")
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


admin.site.site_header = "alex.volkmann.com"
