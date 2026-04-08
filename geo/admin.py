from django.contrib import admin
from .models import Continent, Country, Clue, UserProgress, Course


class ClueInline(admin.TabularInline):
    model = Clue
    extra = 1
    fields = ('title', 'category', 'importance', 'image', 'description', 'order')


class CountryInline(admin.TabularInline):
    model = Country
    extra = 1
    fields = ('name', 'slug', 'flag_emoji', 'drive_side', 'difficulty', 'order')
    show_change_link = True


@admin.register(Continent)
class ContinentAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [CountryInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'order')
        }),
        ('Inhalt', {
            'fields': ('description', 'cover_image', 'drive_side_note')
        }),
    )


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('flag_emoji', 'name', 'continent', 'drive_side', 'difficulty', 'order')
    list_filter = ('continent', 'drive_side', 'difficulty')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ClueInline]
    fieldsets = (
        (None, {
            'fields': ('continent', 'name', 'slug', 'flag_emoji', 'order')
        }),
        ('Details', {
            'fields': ('drive_side', 'difficulty', 'short_summary')
        }),
    )


@admin.register(Clue)
class ClueAdmin(admin.ModelAdmin):
    list_display = ('title', 'country', 'category', 'importance', 'order')
    list_filter = ('category', 'importance', 'country__continent')
    search_fields = ('title', 'country__name')
    fieldsets = (
        (None, {
            'fields': ('country', 'title', 'category', 'importance', 'order')
        }),
        ('Inhalt', {
            'fields': ('description', 'image')
        }),
    )


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'clue', 'known', 'seen_at')
    list_filter = ('known', 'clue__country__continent')
    search_fields = ('user__username', 'clue__title')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'continent', 'difficulty', 'order', 'clue_count')
    list_filter = ('continent', 'difficulty')
    search_fields = ('name',)
    filter_horizontal = ('clues',)
    fieldsets = (
        (None, {
            'fields': ('continent', 'name', 'difficulty', 'order', 'description')
        }),
        ('Clues', {
            'fields': ('clues',)
        }),
    )

    def clue_count(self, obj):
        return obj.clues.count()
    clue_count.short_description = 'Clues'
