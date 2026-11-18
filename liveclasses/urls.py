from django.urls import path
from . import views

urlpatterns = [
    path("", views.live_list, name="live_list"),
    path("<int:pk>/join/", views.join_class, name="join_class"),

    # Live-class attendance  →  /live/<id>/attend/start/  (no double "live/")
    path("<int:live_class_id>/attend/start/",
         views.start_live_attendance, name='start_live_attendance'),
    path("<int:live_class_id>/attend/heartbeat/",
         views.heartbeat_live_attendance, name='heartbeat_live_attendance'),
    path("<int:live_class_id>/attendance/",
         views.live_class_attendance_report, name='live_class_attendance_report'),
]