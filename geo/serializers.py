from rest_framework import serializers
from .models import Continent, Country, Clue, UserProgress, Course


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
        fields = ['id', 'name', 'slug', 'flag_emoji', 'drive_side', 'drive_side_display',
                  'difficulty', 'difficulty_display', 'short_summary', 'order',
                  'clues', 'clue_count']


class CountryListSerializer(serializers.ModelSerializer):
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    clue_count = serializers.IntegerField(source='clues.count', read_only=True)

    class Meta:
        model = Country
        fields = ['id', 'name', 'slug', 'flag_emoji', 'drive_side',
                  'difficulty', 'difficulty_display', 'short_summary', 'clue_count']


class ContinentSerializer(serializers.ModelSerializer):
    countries = CountryListSerializer(many=True, read_only=True)
    country_count = serializers.IntegerField(source='countries.count', read_only=True)

    class Meta:
        model = Continent
        fields = ['id', 'name', 'slug', 'description', 'cover_image',
                  'drive_side_note', 'order', 'countries', 'country_count']


class ContinentListSerializer(serializers.ModelSerializer):
    country_count = serializers.IntegerField(source='countries.count', read_only=True)

    class Meta:
        model = Continent
        fields = ['id', 'name', 'slug', 'description', 'cover_image',
                  'drive_side_note', 'order', 'country_count']


class UserProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = ['id', 'clue', 'known', 'seen_at']
        read_only_fields = ['seen_at']


class CourseSerializer(serializers.ModelSerializer):
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    clue_count = serializers.IntegerField(source='clues.count', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'difficulty', 'difficulty_display', 'clue_count', 'order']


class CoursePracticeClueSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    country_id = serializers.IntegerField(source='country.id', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    importance_display = serializers.CharField(source='get_importance_display', read_only=True)

    class Meta:
        model = Clue
        fields = ['id', 'title', 'category', 'category_display', 'description',
                  'image', 'importance', 'importance_display', 'order',
                  'country_name', 'country_id']
