from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("meetings/", views.parent_meetings, name="parent_meetings"),
    path("meetings/request/", views.request_meeting, name="request_meeting"), 
    path("link-child/", views.link_child, name="link_child"),
    path("meetings/update/<int:meeting_id>/<str:status>/", views.update_meeting_status, name="update_meeting_status"),
    path("notifications/", views.notification_list, name="notification_list"),
    path("notifications/send/<int:course_id>/", views.send_teacher_notification, name="send_teacher_notification"),
    path("meetings/create/", views.create_meeting, name="create_meeting"),
    path('admin-dashboard/audit-logs/', views.audit_log_list, name='audit_log_list'),
    path('teacher/students/', views.teacher_student_list, name='teacher_student_list'),
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/send/', views.send_message, name='send_message'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('report-card/download/', views.download_report_card, name='download_report_card'),
    path('report-card/download/<int:student_id>/',
         views.download_report_card, name='download_report_card_for_child'),
    path('report-cards/download-all/',
         views.download_all_children_report_cards,
         name='download_all_children_report_cards'),
    path('teacher/class-report/', views.download_class_report,
         name='download_class_report'),

    # NEW: Teacher revenue
    path('teacher/revenue/', views.teacher_revenue_detail,
         name='teacher_revenue_detail'),
    path('teacher/revenue/statement/', views.download_payout_statement,
         name='download_payout_statement'),
]