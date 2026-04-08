from django.urls import path
from . import api_views

urlpatterns = [
    path('continents/', api_views.ContinentListView.as_view(), name='geo-continents'),
    path('continents/<slug:slug>/', api_views.ContinentDetailView.as_view(), name='geo-continent-detail'),
    path('continents/<slug:slug>/courses/', api_views.ContinentCoursesView.as_view(), name='geo-courses'),
    path('countries/<slug:slug>/', api_views.CountryDetailView.as_view(), name='geo-country-detail'),
    path('practice/', api_views.PracticeCluesView.as_view(), name='geo-practice'),
    path('practice/course/<int:course_id>/all/', api_views.CoursePracticeAllCluesView.as_view(), name='geo-practice-course-all'),
    path('practice/course/<int:course_id>/', api_views.PracticeCourseCluessView.as_view(), name='geo-practice-course'),
    path('progress/', api_views.UserProgressView.as_view(), name='geo-progress'),
]
