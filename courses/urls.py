from django.urls import path
from . import views

urlpatterns = [
    path("", views.course_list, name="course_list"),
    path("<int:pk>/", views.course_detail, name="course_detail"),

    path("lecture/<int:pk>/", views.lecture_view, name="lecture_view"),
    path("lecture/<int:pk>/complete/", views.mark_lecture_complete, name="mark_lecture_complete"),

    path("<int:course_id>/discussions/", views.discussion_list, name="discussion_list"),
    path("discussions/<int:discussion_id>/", views.discussion_detail, name="discussion_detail"),

    # Certificates
    path("<int:course_id>/certificate/", views.download_certificate, name="download_certificate"),
    path("my-certificates/", views.my_certificates, name="my_certificates"),
    path("certificate/verify/<str:serial>/", views.verify_certificate, name="verify_certificate"),

    path("<int:pk>/manage/", views.teacher_manage_course, name="teacher_manage_course"),
]