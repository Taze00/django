from rest_framework import serializers
from .models import Continent, Country, Clue, UserProgress, Course, Region


class ClueSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    importance_display = serializers.CharField(source='get_importance_display', read_only=True)

    class Meta:
        model = Clue
        fields = ['id', 'title', 'category', 'category_display', 'description',
                  'image', 'importance', 'importance_display', 'order']


class CountrySerializer(serializers.ModelSerializer):
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    drive_side_display = serializers.CharField(source='get_drive_side_display', read_only=True)
    clues = ClueSerializer(many=True, read_only=True)
    clue_count = serializers.IntegerField(source='clues.count', read_only=True)

    class Meta:
        model = Country
        fields = ['id', 'name', 'name_de', 'slug', 'flag_emoji', 'drive_side', 'drive_side_display',
                  'difficulty', 'difficulty_display', 'short_summary', 'map_image', 'domain', 'order',
                  'clues', 'clue_count']


class CountryListSerializer(serializers.ModelSerializer):
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    clue_count = serializers.IntegerField(source='clues.count', read_only=True)
    continent_slug = serializers.CharField(source='continent.slug', read_only=True)

    class Meta:
        model = Country
        fields = ['id', 'name', 'name_de', 'slug', 'flag_emoji', 'drive_side',
                  'difficulty', 'difficulty_display', 'short_summary', 'map_image', 'domain', 'continent_slug', 'clue_count']


class ContinentSerializer(serializers.ModelSerializer):
    countries = CountryListSerializer(many=True, read_only=True)
    country_count = serializers.IntegerField(source='countries.count', read_only=True)

    class Meta:
        model = Continent
        fields = ['id', 'name', 'name_de', 'slug', 'description', 'cover_image',
                  'drive_side_note', 'order', 'countries', 'country_count']


class ContinentListSerializer(serializers.ModelSerializer):
    country_count = serializers.IntegerField(source='countries.count', read_only=True)

    class Meta:
        model = Continent
        fields = ['id', 'name', 'name_de', 'slug', 'description', 'cover_image',
                  'drive_side_note', 'order', 'country_count']


class UserProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = ['id', 'clue', 'known', 'seen_at']
        read_only_fields = ['seen_at']


class CourseSerializer(serializers.ModelSerializer):
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    clue_count = serializers.IntegerField(source='clues.count', read_only=True)
    continent_name = serializers.CharField(source='continent.name', read_only=True, default=None)
    continent_name_de = serializers.CharField(source='continent.name_de', read_only=True, default=None)
    continent_slug = serializers.CharField(source='continent.slug', read_only=True, default=None)
    country_count = serializers.SerializerMethodField()

    def get_country_count(self, obj):
        if obj.course_type in ('flags', 'domains', 'capitals'):
            return obj.continent.countries.count()
        return obj.clues.count()

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'difficulty', 'difficulty_display', 'clue_count', 'country_count', 'course_type', 'order', 'continent_name', 'continent_name_de', 'continent_slug']


class CoursePracticeClueSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    country_name_de = serializers.CharField(source='country.name_de', read_only=True)
    country_id = serializers.IntegerField(source='country.id', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    importance_display = serializers.CharField(source='get_importance_display', read_only=True)
    region_id = serializers.IntegerField(source='region.id', read_only=True, default=None)
    region_name = serializers.CharField(source='region.name', read_only=True, default=None)
    region_map_image = serializers.ImageField(source='region.map_image', read_only=True, default=None)

    class Meta:
        model = Clue
        fields = ['id', 'title', 'category', 'category_display', 'description',
                  'image', 'importance', 'importance_display', 'order',
                  'country_name', 'country_name_de', 'country_id', 'question',
                  'region_id', 'region_name', 'region_map_image']
