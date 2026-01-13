from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    ExerciseViewSet, ProgressionViewSet, WorkoutViewSet,
    WorkoutSetViewSet, UserProfileViewSet, UserViewSet, StatsViewSet
)

router = DefaultRouter()
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'progressions', ProgressionViewSet, basename='progression')
router.register(r'workouts', WorkoutViewSet, basename='workout')
router.register(r'sets', WorkoutSetViewSet, basename='set')

urlpatterns = [
    # JWT Token endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User endpoints
    path('user/me/', UserViewSet.as_view({'get': 'me', 'put': 'me'}), name='user_me'),
    path('user/profile/', UserProfileViewSet.as_view({'get': 'profile', 'put': 'profile'}), name='user_profile'),
    path('user/progressions/', UserProfileViewSet.as_view({'get': 'progressions'}), name='user_progressions'),
    path('user/check-upgrades/', UserProfileViewSet.as_view({'get': 'check_upgrades'}), name='check_upgrades'),
    path('user/upgrade-progression/', UserProfileViewSet.as_view({'post': 'upgrade_progression'}), name='upgrade_progression'),

    # Stats endpoints
    path('stats/overview/', StatsViewSet.as_view({'get': 'overview'}), name='stats_overview'),
    path('stats/exercise-progress/', StatsViewSet.as_view({'get': 'exercise_progress'}), name='exercise_progress'),
    path('stats/progression-history/', StatsViewSet.as_view({'get': 'progression_history'}), name='progression_history'),

    # Router URLs
    path('', include(router.urls)),
]
