from rest_framework import generics, status
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
import random

from .models import Continent, Country, Clue, UserProgress, Course, CourseCardProgress
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


class CountryCoursesView(generics.GenericAPIView):
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

    def get(self, request, slug):
        # Only show courses where >50% of clues belong to this country
        candidate_courses = Course.objects.filter(
            clues__country__slug=slug,
            course_type='clues'
        ).distinct()
        result = []
        for course in candidate_courses:
            total = course.clues.count()
            country_count = course.clues.filter(country__slug=slug).count()
            if total > 0 and country_count / total > 0.5:
                result.append(course)
        serializer = self.get_serializer(result, many=True)
        return Response(serializer.data)


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
        course = get_object_or_404(Course, id=course_id)
        continent_country_names = list(
            Country.objects.filter(continent=course.continent).values_list('name', flat=True)
        )

        if course.course_type in ('flags', 'domains', 'capitals'):
            # Territories that share flag/domain with their parent country - excluded from flags/domains courses
            EXCLUDE_FROM_FLAGS_DOMAINS = {
                'Azores', 'Madeira', 'Svalbard',           # share PT/NO flag+domain
                'Alaska', 'Hawaii', 'US Minor Outlying Islands',  # share USA flag+domain
                'Guam', 'Northern Mariana Islands', 'American Samoa', 'US Virgin Islands',  # USA territories
                'Puerto Rico',                              # USA territory (.com)
                'Saint Pierre and Miquelon',               # France territory
                'Reunion', 'Martinique',                   # France territories
                'Christmas Island', 'Cocos Islands',       # Australia territories
                'Falkland Islands', 'South Georgia & Sandwich Islands', 'British Indian Ocean Territory',  # UK territories
                'Gibraltar', 'Jersey', 'Isle of Man', 'Bermuda',  # UK territories
            }
            if course.course_type == 'flags':
                countries = Country.objects.filter(continent=course.continent, flag_emoji__gt='').exclude(name__in=EXCLUDE_FROM_FLAGS_DOMAINS)
            elif course.course_type == 'domains':
                countries = Country.objects.filter(continent=course.continent, domain__gt='').exclude(name__in=EXCLUDE_FROM_FLAGS_DOMAINS)
            elif course.course_type == 'capitals':
                countries = Country.objects.filter(continent=course.continent, capital__gt='')

            cards = []
            for c in countries:
                cards.append({
                    'id': f'{course.course_type}_{c.id}',
                    'country_name': c.name,
                    'country_name_de': c.name_de or c.name,
                    'country_id': c.id,
                    'course_type': course.course_type,
                    'flag_emoji': c.flag_emoji,
                    'domain': c.domain,
                    'capital': c.capital,
                    'image': None,
                    'title': c.name,
                    'description': '',
                    'category': '',
                    'importance': 1,
                    'order': 0,
                })
            country_names_en = [c['country_name'] for c in cards]
            country_names_de = [c['country_name_de'] for c in cards]
            continent_country_names_de = list(
                Country.objects.filter(continent=course.continent).values_list('name_de', flat=True)
            )
            continent_capital_names = list(
                Country.objects.filter(continent=course.continent, capital__gt='').values_list('capital', flat=True)
            )
            return Response({
                'clues': cards,
                'course_type': course.course_type,
                'course_country_names': country_names_en,
                'course_country_names_de': country_names_de,
                'continent_country_names': continent_country_names,
                'continent_country_names_de': continent_country_names_de,
                'continent_capital_names': continent_capital_names,
            })
        else:
            from .serializers import CoursePracticeClueSerializer
            clues = Clue.objects.filter(courses__id=course_id).select_related('country__continent')
            if not clues.exists():
                return Response({'detail': 'Keine Karten in diesem Kurs.'}, status=status.HTTP_404_NOT_FOUND)

            serializer = CoursePracticeClueSerializer(clues, many=True, context={'request': request})
            course_country_names = list(clues.values_list('country__name', flat=True).distinct())
            return Response({
                'clues': serializer.data,
                'course_type': course.course_type,
                'course_country_names': course_country_names,
                'continent_country_names': continent_country_names,
            })


class CourseCardProgressView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        """Return stage/streak for all cards in this course for the user."""
        rows = CourseCardProgress.objects.filter(
            user=request.user, course_id=course_id
        ).values('country_id', 'stage', 'streak', 'learned')
        return Response({row['country_id']: {'stage': row['stage'], 'streak': row['streak'], 'learned': row['learned']} for row in rows})

    def post(self, request, course_id):
        """Save stage/streak for a card."""
        country_id = request.data.get('country_id')
        stage = request.data.get('stage', 1)
        streak = request.data.get('streak', 0)
        learned = stage == 'learned' or request.data.get('learned', False)
        course = get_object_or_404(Course, id=course_id)
        country = get_object_or_404(Country, id=country_id)
        CourseCardProgress.objects.update_or_create(
            user=request.user, course=course, country=country,
            defaults={'stage': 0 if stage == 'learned' else int(stage), 'streak': streak, 'learned': bool(learned)}
        )
        return Response({'ok': True})


class AllCoursesView(generics.GenericAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = Course.objects.select_related('continent').all()
        serializer = CourseSerializer(courses, many=True)
        data = serializer.data

        # Annotate with progress for this user
        # For clue courses: count learned clues
        learned_clue_ids = set(UserProgress.objects.filter(
            user=request.user, known=True
        ).values_list('clue_id', flat=True))

        # For card courses: count learned countries per course
        card_progress = CourseCardProgress.objects.filter(
            user=request.user, learned=True
        ).values('course_id', 'country_id')
        learned_by_course = {}
        for row in card_progress:
            learned_by_course.setdefault(row['course_id'], set()).add(row['country_id'])

        result = []
        for course_data, course_obj in zip(data, courses):
            d = dict(course_data)
            ct = course_obj.course_type
            if ct == 'clues':
                clue_ids = set(course_obj.clues.values_list('id', flat=True))
                d['learned_count'] = len(clue_ids & learned_clue_ids)
                d['total_count'] = len(clue_ids)
            else:
                learned = learned_by_course.get(course_obj.id, set())
                d['learned_count'] = len(learned)
                d['total_count'] = course_obj.continent.countries.count()
            result.append(d)

        return Response(result)


class DomainSearchView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip().lower()
        if not query:
            return Response([])
        # Add leading dot if missing
        if not query.startswith('.'):
            query = '.' + query
        countries = Country.objects.filter(domain__iexact=query).select_related('continent')
        from .serializers import CountryListSerializer
        serializer = CountryListSerializer(countries, many=True, context={'request': request})
        return Response(serializer.data)


class GlobalSearchView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from .serializers import CountryListSerializer
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 1:
            return Response([])

        q_lower = query.lower()
        q_dot = ('.' + q_lower) if not q_lower.startswith('.') else q_lower

        from django.db.models import Case, When, IntegerField
        countries = Country.objects.select_related('continent').annotate(
            relevance=Case(
                When(domain__iexact=q_dot, then=0),
                When(name__istartswith=query, then=1),
                When(name_de__istartswith=query, then=1),
                When(name__icontains=query, then=2),
                When(name_de__icontains=query, then=2),
                When(domain__icontains=q_lower, then=3),
                default=4,
                output_field=IntegerField(),
            )
        ).filter(
            Q(name__icontains=query) |
            Q(name_de__icontains=query) |
            Q(domain__icontains=q_lower) |
            Q(domain__iexact=q_dot)
        ).order_by('relevance', 'name')[:10]

        serializer = CountryListSerializer(countries, many=True, context={'request': request})
        return Response(serializer.data)
