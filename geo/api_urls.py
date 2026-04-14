from django.urls import path
from . import api_views

urlpatterns = [
    path('continents/', api_views.ContinentListView.as_view(), name='geo-continents'),
    path('continents/<slug:slug>/', api_views.ContinentDetailView.as_view(), name='geo-continent-detail'),
    path('continents/<slug:slug>/courses/', api_views.ContinentCoursesView.as_view(), name='geo-courses'),
    path('countries/<slug:slug>/', api_views.CountryDetailView.as_view(), name='geo-country-detail'),
    path('countries/<slug:slug>/courses/', api_views.CountryCoursesView.as_view(), name='geo-country-courses'),
    path('practice/', api_views.PracticeCluesView.as_view(), name='geo-practice'),
    path('practice/course/<int:course_id>/all/', api_views.CoursePracticeAllCluesView.as_view(), name='geo-practice-course-all'),
    path('practice/course/<int:course_id>/', api_views.PracticeCourseCluessView.as_view(), name='geo-practice-course'),
    path('progress/', api_views.UserProgressView.as_view(), name='geo-progress'),
    path('course-progress/<int:course_id>/', api_views.CourseCardProgressView.as_view(), name='geo-course-progress'),
    path('courses/', api_views.AllCoursesView.as_view(), name='geo-all-courses'),
    path('search/', api_views.GlobalSearchView.as_view(), name='geo-search'),
    path('domain-search/', api_views.DomainSearchView.as_view(), name='geo-domain-search'),

    path('countries/<slug:slug>/clues/', api_views.ClueCreateView.as_view(), name='geo-clue-create'),
    path('clues/<int:clue_id>/', api_views.ClueDetailView.as_view(), name='geo-clue-detail'),
    path('clues/<int:clue_id>/image/', api_views.ClueImageUploadView.as_view(), name='geo-clue-image'),
    path('user-courses/', api_views.UserCourseListCreateView.as_view(), name='geo-user-course-list'),
    path('user-courses/<int:course_id>/', api_views.UserCourseDetailView.as_view(), name='geo-user-course-detail'),
    path('clue-search/', api_views.ClueSearchView.as_view(), name='geo-clue-search'),
    path('my-courses/', api_views.UserCoursesView.as_view(), name='geo-my-courses'),
]
