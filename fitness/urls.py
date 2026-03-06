from django.urls import path, include
from rest_framework.routers import DefaultRouter
from fitness.views import ExerciseViewSet, UserProgressionViewSet, WorkoutViewSet, user_detail

router = DefaultRouter()
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'user-progressions', UserProgressionViewSet, basename='user-progression')
router.register(r'workouts', WorkoutViewSet, basename='workout')

urlpatterns = [
    path('', include(router.urls)),
    path('user/', user_detail, name='user-detail'),
]
