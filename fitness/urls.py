from django.urls import path, include
from rest_framework.routers import DefaultRouter
from fitness.views import ExerciseViewSet, UserProgressionViewSet, WorkoutViewSet, user_detail, upload_profile_picture, delete_profile_picture, user_settings, complete_onboarding, reset_onboarding

router = DefaultRouter()
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'user-progressions', UserProgressionViewSet, basename='user-progression')
router.register(r'workouts', WorkoutViewSet, basename='workout')

urlpatterns = [
    path('', include(router.urls)),
    path('user/', user_detail, name='user-detail'),
    path('profile/picture/upload/', upload_profile_picture, name='upload-profile-picture'),
    path('profile/picture/delete/', delete_profile_picture, name='delete-profile-picture'),
    path('profile/settings/', user_settings, name='user-settings'),
    path('onboarding/complete/', complete_onboarding, name='complete-onboarding'),
    path('onboarding/reset/', reset_onboarding, name='reset-onboarding'),
]
