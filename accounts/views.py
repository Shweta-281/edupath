from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

# Import all your forms
from .forms import RegisterForm, UserUpdateForm, CustomPasswordChangeForm

# accounts/views.py
from .models import User
from django.shortcuts import get_object_or_404
from courses.models import Course

class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/dashboard/"
    



def register_view(request):
    if request.user.is_authenticated:
        return redirect("/dashboard/")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # SAFE CHECK: Prevents crash if profile isn't ready or if it's not a student
            board_name = user.student_profile.board if hasattr(user, 'student_profile') else 'EduPath'
            
            messages.success(request, f"Welcome to EduPath! You are registered under the {board_name} board.")
            return redirect("/dashboard/")
        else:
            messages.error(request, "Registration failed. Please check the errors below.")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def profile_view(request):
    if request.method == 'POST':
        # 1. Handle Profile Information Update
        if 'update_profile' in request.POST:
            u_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
            if u_form.is_valid():
                u_form.save()
                messages.success(request, "✅ Profile updated successfully!")
                return redirect('profile')
                
        # 2. Handle Password Change
        elif 'change_password' in request.POST:
            p_form = CustomPasswordChangeForm(request.user, request.POST)
            if p_form.is_valid():
                user = p_form.save()
                update_session_auth_hash(request, user) # Keeps the user logged in
                messages.success(request, "🔒 Password changed successfully!")
                return redirect('profile')
            else:
                messages.error(request, "❌ Please correct the errors below.")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = CustomPasswordChangeForm(request.user)

    return render(request, 'accounts/profile.html', {
        'u_form': u_form,
        'p_form': p_form
    })
    

@login_required
def teacher_profile(request, teacher_id):
    # REMOVED the 'role=teacher' check so it doesn't crash if it's an Admin
    teacher = get_object_or_404(User, id=teacher_id) 
    courses = Course.objects.filter(teacher=teacher)
    
    return render(request, 'accounts/teacher_public_profile.html', {
        'teacher': teacher,
        'courses': courses
    })