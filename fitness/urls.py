from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    ExerciseViewSet, ProgressionViewSet, WorkoutViewSet, UserProfileViewSet,
    UserExerciseProgressionViewSet
)

router = DefaultRouter()
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'progressions', ProgressionViewSet, basename='progression')
router.register(r'workouts', WorkoutViewSet, basename='workout')
router.register(r'user-progressions', UserExerciseProgressionViewSet, basename='user-progression')

urlpatterns = [
    # JWT Token endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User endpoints
    path('user/profile/', UserProfileViewSet.as_view({'get': 'profile', 'put': 'profile'}), name='user_profile'),
    path('user/me/', UserProfileViewSet.as_view({'get': 'me', 'put': 'me'}), name='user_me'),
    path('user/progressions/', UserProfileViewSet.as_view({'get': 'progressions'}), name='user_progressions'),
    path('user/check-upgrades/', UserProfileViewSet.as_view({'get': 'check_upgrades'}), name='check_upgrades'),
    path('user/upgrade-progression/', UserProfileViewSet.as_view({'post': 'upgrade_progression'}), name='upgrade_progression'),

    # Router URLs
    path('', include(router.urls)),
]
