from django.urls import path
from . import views
urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path('teacher/<int:teacher_id>/', views.teacher_profile, name='teacher_profile'),
]