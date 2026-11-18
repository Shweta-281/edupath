from django.urls import path
from . import views

urlpatterns = [
    path("", views.quiz_list, name="quiz_list"),
    path("start/<int:pk>/", views.start_quiz, name="start_quiz"),
    path("submit/<int:attempt_id>/", views.submit_quiz, name="submit_quiz"),
    path("result/<int:pk>/", views.quiz_result, name="quiz_result"),

    # Teacher quiz management
    path("teacher/", views.teacher_quiz_list, name="teacher_quiz_list"),
    path("teacher/create/", views.teacher_create_quiz, name="teacher_create_quiz"),
    path("teacher/<int:pk>/", views.teacher_quiz_detail, name="teacher_quiz_detail"),
    path("teacher/<int:pk>/regenerate/", views.teacher_regenerate_quiz, name="teacher_regenerate_quiz"),
    
    # Assignment URLs
    path('assignments/teacher/', views.teacher_assignment_list, name='teacher_assignment_list'),
    path('assignments/teacher/create/', views.teacher_create_assignment, name='teacher_create_assignment'),
    path('assignments/teacher/<int:pk>/', views.teacher_assignment_detail, name='teacher_assignment_detail'),
    path('assignments/teacher/grade/<int:submission_id>/', views.grade_submission, name='grade_submission'),
    
    path('assignments/student/', views.student_assignment_list, name='student_assignment_list'),
    path('assignments/student/submit/<int:pk>/', views.submit_assignment, name='submit_assignment'),
]