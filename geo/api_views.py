from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
import random

from .models import Continent, Country, Clue, UserProgress, Course
from .serializers import (
    ContinentSerializer, ContinentListSerializer,
    CountrySerializer, ClueSerializer, UserProgressSerializer,
    CourseSerializer
)


class ContinentListView(generics.ListAPIView):
    queryset = Continent.objects.all()
    serializer_class = ContinentListSerializer
    permission_classes = [AllowAny]


class ContinentDetailView(generics.RetrieveAPIView):
    queryset = Continent.objects.prefetch_related('countries')
    serializer_class = ContinentSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]


class CountryDetailView(generics.RetrieveAPIView):
    queryset = Country.objects.prefetch_related('clues')
    serializer_class = CountrySerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]


class PracticeCluesView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        continent_slug = request.query_params.get('continent')
        category = request.query_params.get('category')
        only_unknown = request.query_params.get('only_unknown') == 'true'

        clues = Clue.objects.select_related('country__continent').all()

        if continent_slug:
            clues = clues.filter(country__continent__slug=continent_slug)
        if category:
            clues = clues.filter(category=category)
        if only_unknown and request.user.is_authenticated:
            known_ids = UserProgress.objects.filter(
                user=request.user, known=True
            ).values_list('clue_id', flat=True)
            clues = clues.exclude(id__in=known_ids)

        clues = list(clues)
        if not clues:
            return Response({'detail': 'Keine Karten gefunden.'}, status=status.HTTP_404_NOT_FOUND)

        clue = random.choice(clues)
        serializer = ClueSerializer(clue, context={'request': request})
        return Response(serializer.data)


class UserProgressView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProgressSerializer

    def post(self, request):
        clue_id = request.data.get('clue')
        known = request.data.get('known', False)

        clue = get_object_or_404(Clue, id=clue_id)
        progress, _ = UserProgress.objects.update_or_create(
            user=request.user,
            clue=clue,
            defaults={'known': known}
        )
        serializer = self.get_serializer(progress)
        return Response(serializer.data)

    def get(self, request):
        progress = UserProgress.objects.filter(user=request.user).select_related('clue')
        serializer = self.get_serializer(progress, many=True)
        return Response(serializer.data)


class ContinentCoursesView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Course.objects.filter(continent__slug=self.kwargs['slug'])


class PracticeCourseCluessView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        clues = Clue.objects.filter(courses__id=course_id).select_related('country')
        if not clues:
            return Response({'detail': 'Keine Karten in diesem Kurs.'}, status=status.HTTP_404_NOT_FOUND)
        import random
        clue = random.choice(list(clues))
        serializer = ClueSerializer(clue, context={'request': request})
        return Response(serializer.data)


class CoursePracticeAllCluesView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        from .serializers import CoursePracticeClueSerializer
        clues = Clue.objects.filter(courses__id=course_id).select_related('country__continent')
        if not clues.exists():
            return Response({'detail': 'Keine Karten in diesem Kurs.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CoursePracticeClueSerializer(clues, many=True, context={'request': request})
        course_country_names = list(clues.values_list('country__name', flat=True).distinct())
        continent_id = clues.first().country.continent_id
        continent_country_names = list(
            Country.objects.filter(continent_id=continent_id).values_list('name', flat=True)
        )
        return Response({
            'clues': serializer.data,
            'course_country_names': course_country_names,
            'continent_country_names': continent_country_names,
        })
