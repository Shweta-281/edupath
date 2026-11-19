import json
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from courses.models import Course, Enrollment
from assessments.models import QuizAttempt
from attendance.models import Attendance
from payments.models import Payment
from .forms import MeetingRequestForm
from liveclasses.models import ParentMeeting
from django.contrib import messages
from accounts.models import User
from .forms import LinkChildForm
from django.utils import timezone
from django.shortcuts import get_object_or_404
from liveclasses.models import ParentMeeting
from .models import Notification
from accounts.models import StudentProfile
from .forms import MeetingForm
from liveclasses.models import LiveClass
from .models import Notification
from courses.models import Enrollment
from django.urls import reverse
from liveclasses.models import LiveClass, ParentMeeting
from assessments.models import QuizAttempt, Assignment, Submission

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from accounts.models import User, StudentProfile
from courses.models import Course, Enrollment
from payments.models import Payment

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .utils import generate_combined_report_card, generate_report_card
from assessments.models import QuizAttempt
from attendance.models import Attendance
from django.contrib import messages

from .utils import (
    generate_report_card,
    generate_combined_report_card,
    generate_class_report,
)

from decimal import Decimal

def home(request):
    featured = Course.objects.all()[:6]
    return render(request, "home.html", {"featured": featured})

@login_required
def dashboard(request):
    # 1. Superusers always go to the admin dashboard
    if request.user.is_superuser:
        return admin_dashboard(request)
        
    role = request.user.role
    
    # 2. Safely route based on role, checking if the profile actually exists
    if role == "student": 
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, "Your student profile is missing. Please contact support.")
            return redirect('home')
        return student_dashboard(request)
        
    if role == "teacher": 
        if not hasattr(request.user, 'teacher_profile'):
            messages.error(request, "Your teacher profile is missing. Please contact support.")
            return redirect('home')
        return teacher_dashboard(request)
        
    if role == "parent": 
        if not hasattr(request.user, 'parent_profile'):
            messages.error(request, "Your parent profile is missing. Please contact support.")
            return redirect('home')
        return parent_dashboard(request)
        
    return admin_dashboard(request) 

def student_dashboard(request):
    student = request.user.student_profile
    
    # 1. Fetch enrollments
    enrollments = Enrollment.objects.filter(student=student).select_related("course")
    
    # 2. Calculate progress for each course
    enrollment_data = []
    for e in enrollments:
        progress = e.course.get_progress(student)
        enrollment_data.append({
            'enrollment': e,
            'progress': progress
        })

    # 3. Existing Logic
    attempts = QuizAttempt.objects.filter(student=student).order_by("-started_at")[:5]
    attendance = Attendance.objects.filter(student=student)
    total = attendance.count()
    present = attendance.filter(status="present").count()
    pct = round((present / total * 100) if total else 0, 1)
    
    # 4. AI Risk & Assignments
    risk_status = student.risk_status
    
    enrolled_course_ids = enrollments.values_list('course_id', flat=True)
    submitted_assignment_ids = Submission.objects.filter(student=student).values_list('assignment_id', flat=True)
    upcoming_assignments = Assignment.objects.filter(
        course_id__in=enrolled_course_ids,
        due_date__gte=timezone.now()
    ).exclude(id__in=submitted_assignment_ids).order_by('due_date')[:3]
    
    return render(request, "dashboard/student.html", {
        "enrollment_data": enrollment_data,  # Note the change here
        "attempts": attempts, 
        "attendance_percent": pct,
        "risk_status": risk_status,
        "upcoming_assignments": upcoming_assignments,
    })
    
    
def teacher_dashboard(request):
    from liveclasses.models import ParentMeeting
    from assessments.models import Assignment, Submission, Quiz, QuizAttempt
    from payments.models import Payment
    from django.db.models import Sum

    # 1. Existing Data
    courses = Course.objects.filter(teacher=request.user)
    meetings = ParentMeeting.objects.filter(teacher=request.user).order_by('-created_at')

    # 2. Analytics
    total_students = Enrollment.objects.filter(course__in=courses, is_active=True).values('student').distinct().count()

    assignments = Assignment.objects.filter(course__in=courses)
    total_assignments = assignments.count()
    submissions = Submission.objects.filter(assignment__in=assignments)
    pending_grading = submissions.filter(grade__isnull=True).count()

    quizzes = Quiz.objects.filter(course__in=courses)
    attempts = QuizAttempt.objects.filter(quiz__in=quizzes, completed_at__isnull=False)
    avg_quiz_score = 0
    if attempts.exists():
        avg_quiz_score = round(sum([a.percentage() for a in attempts]) / attempts.count(), 1)

    # 3. Revenue (this month + lifetime)
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    paid_qs = Payment.objects.filter(course__in=courses, status="paid")
    lifetime_gross = paid_qs.aggregate(s=Sum('amount'))['s'] or Decimal("0")
    month_gross = paid_qs.filter(created_at__gte=month_start).aggregate(s=Sum('amount'))['s'] or Decimal("0")

    lifetime_teacher = Decimal("0")
    month_teacher = Decimal("0")
    for p in paid_qs.select_related('course'):
        rate = Decimal(p.course.revenue_share_percent) / Decimal(100)
        lifetime_teacher += p.amount * rate
        if p.created_at >= month_start:
            month_teacher += p.amount * rate
    lifetime_teacher = lifetime_teacher.quantize(Decimal("0.01"))
    month_teacher = month_teacher.quantize(Decimal("0.01"))

    context = {
        "courses": courses,
        "meetings": meetings,
        "total_students": total_students,
        "total_assignments": total_assignments,
        "pending_grading": pending_grading,
        "avg_quiz_score": avg_quiz_score,
        "submitted_count": submissions.exclude(grade__isnull=True).count(),
        # NEW
        "lifetime_teacher_earnings": lifetime_teacher,
        "month_teacher_earnings": month_teacher,
    }
    return render(request, "dashboard/teacher.html", context)


def parent_dashboard(request):
    from accounts.models import StudentProfile

    profiles = (
        StudentProfile.objects
        .filter(parent=request.user)
        .select_related("user")
    )
    child_data = []

    for profile in profiles:
        child = profile.user

        attempts = QuizAttempt.objects.filter(student=profile).order_by("-started_at")
        attendance = Attendance.objects.filter(student=profile)

        total   = attendance.count()
        present = attendance.filter(status="present").count()
        absent  = attendance.filter(status="absent").count()
        late    = attendance.filter(status="late").count()
        pct = round((present / total * 100) if total else 0, 1)

        recent = list(attempts[:6])[::-1]
        child_data.append({
            "child": child,
            "profile": profile,
            "enrollments": Enrollment.objects.filter(student=profile).count(),
            "attempts": attempts[:5],
            "attendance_percent": pct,
            "quiz_labels": json.dumps([a.quiz.title[:22] for a in recent]),
            "quiz_percentages": json.dumps([a.percentage() for a in recent]),
            "attendance_present": present,
            "attendance_absent":  absent,
            "attendance_late":    late,
        })

    return render(request, "dashboard/parent.html", {"child_data": child_data})


@login_required
def parent_meetings(request):
    if request.user.role != 'parent':
        return redirect('dashboard')
    
    # 1. Fetch PTM requests
    meetings = ParentMeeting.objects.filter(parent=request.user).order_by('-created_at')
    
    # 2. Fetch Live Classes scheduled by teachers for their children
    # Get the children linked to this parent
    children = request.user.children.all()
    child_courses = []
    for child in children:
        # Get all courses the child is enrolled in
        enrollments = Enrollment.objects.filter(student=child, is_active=True)
        for e in enrollments:
            child_courses.append(e.course.id)

    # Fetch upcoming live classes for those courses
    live_classes = LiveClass.objects.filter(course_id__in=child_courses).order_by('scheduled_at')
    
    return render(request, "dashboard/meetings.html", {
        "meetings": meetings,
        "live_classes": live_classes
    })
    
@login_required
def request_meeting(request):
    if request.user.role != 'parent':
        return redirect('dashboard')

    if request.method == "POST":
        form = MeetingRequestForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.parent = request.user
            meeting.save()
            messages.success(request, "✅ Meeting request sent successfully!") 
            return redirect('parent_meetings')
    else:
        form = MeetingRequestForm()

    return render(request, "dashboard/request_meeting.html", {"form": form})


@staff_member_required
def admin_dashboard(request):
    # 1. Core Stats
    total_revenue = Payment.objects.filter(status="paid").aggregate(Sum('amount'))['amount__sum'] or 0
    total_students = StudentProfile.objects.count()
    total_courses = Course.objects.count()
    total_enrollments = Enrollment.objects.filter(is_active=True).count()

    # 2. Revenue Chart Data (Last 6 Months)
    # (This groups payments by month. Assuming you have a 'created_at' field on Payment)
    six_months_ago = timezone.now() - timedelta(days=180)
    recent_payments = Payment.objects.filter(status="paid", created_at__gte=six_months_ago).order_by('created_at')
    
    revenue_labels = []
    revenue_data = []
    
    # Simplified grouping for the chart (Grouping by Date for demo)
    for p in recent_payments:
        date_str = p.created_at.strftime("%b %d")
        if date_str in revenue_labels:
            idx = revenue_labels.index(date_str)
            revenue_data[idx] += float(p.amount)
        else:
            revenue_labels.append(date_str)
            revenue_data.append(float(p.amount))

    # 3. Top 5 Courses by Enrollment
    top_courses = Course.objects.annotate(
        enroll_count=Count('enrollments')
    ).order_by('-enroll_count')[:5]

    # 4. Recent Activity
    recent_enrollments = Enrollment.objects.select_related("student__user", "course").order_by("-enrolled_at")[:5]
    recent_payments = Payment.objects.filter(status="paid").select_related("student__user", "course").order_by("-created_at")[:5]

    context = {
        "total_revenue": total_revenue,
        "total_students": total_students,
        "total_courses": total_courses,
        "total_enrollments": total_enrollments,
        "recent_enrollments": recent_enrollments,
        "recent_payments": recent_payments,
        "top_courses": top_courses,
        "revenue_labels": json.dumps(revenue_labels),
        "revenue_data": json.dumps(revenue_data),
    }
    
    return render(request, "dashboard/admin.html", context)
    

@login_required
def link_child(request):
    if request.user.role != 'parent':
        return redirect('dashboard')

    if request.method == "POST":
        form = LinkChildForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['student_email']
            try:
                # Find the student by email
                student_user = User.objects.get(email=email, role='student')
                profile = student_user.student_profile
                
                # Check if they are already linked
                if profile.parent:
                    messages.error(request, "This student is already linked to a parent.")
                else:
                    profile.parent = request.user
                    profile.save()
                    messages.success(request, f"✅ Successfully linked {student_user.get_full_name() or student_user.username} to your account!")
                    return redirect('dashboard')
            except User.DoesNotExist:
                messages.error(request, "❌ No student found with that email address.")
            except Exception as e:
                messages.error(request, "An error occurred while linking the student.")
    else:
        form = LinkChildForm()

    return render(request, "dashboard/link_child.html", {"form": form})

@login_required
def update_meeting_status(request, meeting_id, status):
    if request.user.role != 'teacher':
        return redirect('dashboard')
        
    meeting = get_object_or_404(ParentMeeting, id=meeting_id, teacher=request.user)
    
    if status in ['approved', 'rejected']:
        meeting.status = status
        meeting.save()
        messages.success(request, f"Meeting successfully {status}!")
        
    return redirect('dashboard')

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user)
    # Mark all as read
    notifications.update(is_read=True)
    return render(request, "dashboard/notifications.html", {"notifications": notifications})

@login_required
def send_teacher_notification(request, course_id):
    if request.user.role != 'teacher':
        return redirect('dashboard')
        
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        
        # Send to all enrolled students
        enrollments = course.enrollments.filter(is_active=True)
        for e in enrollments:
            Notification.objects.create(recipient=e.student.user, title=title, message=message)
            # Optional: Send email here
            
        messages.success(request, f"Notification sent to {enrollments.count()} students!")
        return redirect('dashboard')
        
    return render(request, "dashboard/send_notification.html", {"course": course})

@login_required
def create_meeting(request):
    if request.user.role != 'teacher':
        return redirect('dashboard')

    if request.method == 'POST':
        form = MeetingForm(request.POST, teacher=request.user)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.teacher = request.user
            meeting.save()
            
            # 🔔 Generate the URL to join this specific meeting
            # This uses the 'join_class' URL from your liveclasses app
            meeting_url = reverse('join_class', args=[meeting.id])

            # 🔔 Send Notifications to Students and Parents
            enrollments = Enrollment.objects.filter(course=meeting.course, is_active=True)
            notif_count = 0
            
            for e in enrollments:
                # 1. Notify Student
                Notification.objects.create(
                    recipient=e.student.user,
                    title=f"📅 New Meeting: {meeting.title}",
                    message=f"A new meeting for {meeting.course.title} has been scheduled on {meeting.scheduled_at.strftime('%d %b %Y, %I:%M %p')}. Please join on time.",
                    link=meeting_url
                )
                notif_count += 1
                
                # 2. Notify Parent (if linked)
                if e.student.parent:
                    Notification.objects.create(
                        recipient=e.student.parent,
                        title=f"📅 Meeting Scheduled for {e.student.user.username}",
                        message=f"Teacher {request.user.username} scheduled a meeting for {meeting.course.title} on {meeting.scheduled_at.strftime('%d %b %Y, %I:%M %p')}.",
                        link=meeting_url
                    )
                    notif_count += 1

            messages.success(request, f"✅ Meeting scheduled! Sent {notif_count} notifications.")
            return redirect('dashboard')
    else:
        form = MeetingForm(teacher=request.user)

    return render(request, 'dashboard/create_meeting.html', {'form': form})

from accounts.models import AuditLog
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

# Add this to your views
@staff_member_required
def audit_log_list(request):
    # Get the 50 most recent actions
    logs = AuditLog.objects.all().order_by('-timestamp')[:50]
    return render(request, 'dashboard/audit_logs.html', {'logs': logs})

# dashboard/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from courses.models import Enrollment
from assessments.models import QuizAttempt

@login_required
def teacher_student_list(request):
    if request.user.role != 'teacher' and request.user.role != 'admin':
        return redirect('dashboard')
        
    if request.user.role == 'admin':
        enrollments = Enrollment.objects.all().select_related('student__user', 'course')
    else:
        enrollments = Enrollment.objects.filter(
            course__teacher=request.user, 
            is_active=True
        ).select_related('student__user', 'course')

    # Create a dictionary to group courses by student (so we don't list the same student multiple times)
    student_data = {}
    
    for e in enrollments:
        student = e.student
        if student.id not in student_data:
            # Calculate Quiz Average
            attempts = QuizAttempt.objects.filter(student=student, completed_at__isnull=False)
            if attempts.exists():
                avg_score = round(sum([a.percentage() for a in attempts]) / attempts.count(), 1)
            else:
                avg_score = 0

            student_data[student.id] = {
                'student': student,
                'courses': [],
                'risk': student.risk_status,
                'avg_score': avg_score,
                'overall_progress': 0 # Placeholder
            }
        
        # Add the specific course progress
        progress = e.course.get_progress(student)
        student_data[student.id]['courses'].append({
            'title': e.course.title,
            'progress': progress['percentage']
        })

    # Convert to list and sort by risk (High Risk first, then Medium, then Safe)
    risk_order = {'High Risk': 1, 'Medium Risk': 2, 'Safe': 3, 'Unknown': 4}
    students_list = list(student_data.values())
    students_list.sort(key=lambda x: risk_order.get(x['risk']['label'], 4))

    # Chart Data
    high_risk_count = sum(1 for s in students_list if s['risk']['label'] == 'High Risk')
    med_risk_count = sum(1 for s in students_list if s['risk']['label'] == 'Medium Risk')
    safe_count = sum(1 for s in students_list if s['risk']['label'] == 'Safe')

    return render(request, "dashboard/teacher_students.html", {
        "students": students_list,
        "high_risk_count": high_risk_count,
        "med_risk_count": med_risk_count,
        "safe_count": safe_count,
    })
    
@login_required
def download_class_report(request):
    """
    Teacher only. Generates ONE PDF with an overview of all their students
    plus a per-student detail page.
    """
    if request.user.role != 'teacher':
        return redirect('dashboard')

    teacher = request.user
    courses = Course.objects.filter(teacher=teacher)

    if not courses.exists():
        messages.error(request, "You have no courses yet — nothing to report.")
        return redirect('dashboard')

    # Gather enrollments across the teacher's courses, grouped by student
    enrollments = (
        Enrollment.objects
        .filter(course__in=courses, is_active=True)
        .select_related('student__user', 'course')
    )

    students_map = {}
    for e in enrollments:
        sid = e.student.id
        if sid not in students_map:
            students_map[sid] = {
                'student': e.student,
                'courses': [],
            }
        title = e.course.title
        if title not in students_map[sid]['courses']:
            students_map[sid]['courses'].append(title)

    if not students_map:
        messages.error(request, "No students enrolled in your courses yet.")
        return redirect('dashboard')

    # Enrich each student with stats
    students_data = []
    risk_counts = {'High Risk': 0, 'Medium Risk': 0, 'Safe': 0}
    all_scores = []

    for data in students_map.values():
        student = data['student']

        attempts_qs = (
            QuizAttempt.objects
            .filter(student=student, completed_at__isnull=False)
            .order_by('-started_at')
        )
        attempts_list = list(attempts_qs)
        avg_score = (
            round(sum(a.percentage() for a in attempts_list) / len(attempts_list), 1)
            if attempts_list else 0
        )
        all_scores.append(avg_score)

        attendance = Attendance.objects.filter(student=student)
        total = attendance.count()
        present = attendance.filter(status="present").count()
        att_pct = round((present / total * 100) if total else 0, 1)

        risk = student.risk_status or {}
        if risk.get('label') in risk_counts:
            risk_counts[risk['label']] += 1

        students_data.append({
            'student': student,
            'courses': data['courses'],
            'avg_score': avg_score,
            'att_pct': att_pct,
            'risk': risk,
            'attempts': attempts_list[:10],
        })

    # Sort by risk (High first), then by name
    risk_order = {'High Risk': 1, 'Medium Risk': 2, 'Safe': 3}
    students_data.sort(
        key=lambda x: (
            risk_order.get(x['risk'].get('label'), 4),
            (x['student'].user.get_full_name() or x['student'].user.username).lower(),
        )
    )

    summary = {
        'total_students': len(students_data),
        'total_courses': courses.count(),
        'class_avg': round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
        'risk_high': risk_counts['High Risk'],
        'risk_med': risk_counts['Medium Risk'],
        'risk_safe': risk_counts['Safe'],
    }

    return generate_class_report(teacher, students_data, summary)

from accounts.models import Message
from accounts.forms import MessageForm # Adjust import based on where you put the form
from django.contrib import messages

@login_required
def inbox(request):
    received_messages = Message.objects.filter(recipient=request.user).order_by('-timestamp')
    
    # Mark all as read when opening inbox
    received_messages.update(is_read=True)
    
    return render(request, "dashboard/inbox.html", {"messages": received_messages})

@login_required
def send_message(request):
    # NEW: Check if we are replying to someone
    reply_to_id = request.GET.get('reply_to')
    initial_subject = request.GET.get('subject', '')
    
    # Format subject as "Re: [Subject]"
    if initial_subject and not initial_subject.startswith('Re: '):
        initial_subject = f"Re: {initial_subject}"

    if request.method == "POST":
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            
            # NEW: Create a Notification for the recipient!
            Notification.objects.create(
                recipient=message.recipient,
                title="📩 New Message",
                message=f"New message from {request.user.get_full_name() or request.user.username}: {message.subject}",
                link="/dashboard/inbox/" # Assuming your inbox url is /dashboard/inbox/
            )
            
            messages.success(request, "✅ Message sent successfully!")
            return redirect('inbox')
    else:
        # Pre-fill the form if we are replying
        initial_data = {}
        if reply_to_id:
            initial_data['recipient'] = reply_to_id
        if initial_subject:
            initial_data['subject'] = initial_subject
            
        form = MessageForm(user=request.user, initial=initial_data)
        
    return render(request, "dashboard/send_message.html", {"form": form})

@login_required
def leaderboard(request):
    if request.user.role != 'student':
        return redirect('dashboard')
        
    # Get top 10 students by XP
    top_students = StudentProfile.objects.filter(user__role='student').order_by('-xp_points')[:10]
    
    # Find the current student's rank
    current_student = request.user.student_profile
    all_students = StudentProfile.objects.filter(user__role='student').order_by('-xp_points')
    
    rank = 1
    for s in all_students:
        if s.id == current_student.id:
            break
        rank += 1

    return render(request, "dashboard/leaderboard.html", {
        "top_students": top_students,
        "current_student": current_student,
        "my_rank": rank
    })
    

@login_required
def download_report_card(request, student_id=None):
    """
    - Students: downloads their own report card.
    - Parents : downloads a specific linked child's report card
                (student_id = StudentProfile.pk, passed from the parent dashboard).
    """
    if request.user.role == 'student':
        student = request.user.student_profile

    elif request.user.role == 'parent':
        if student_id is None:
            messages.error(request, "No child specified.")
            return redirect('dashboard')
        # Security: this parent must actually be linked to the requested child
        student = get_object_or_404(
            StudentProfile, id=student_id, parent=request.user
        )

    else:
        return redirect('dashboard')

    # --- Stats (identical to your previous logic) ---
    attendance = Attendance.objects.filter(student=student)
    total = attendance.count()
    present = attendance.filter(status="present").count()
    att_pct = round((present / total * 100) if total else 0, 1)

    attempts = QuizAttempt.objects.filter(
        student=student, completed_at__isnull=False
    ).order_by("-started_at")
    avg_score = (
        round(sum([a.percentage() for a in attempts]) / attempts.count(), 1)
        if attempts.exists() else 0
    )

    return generate_report_card(student, att_pct, avg_score, attempts[:10])

@login_required
def download_all_children_report_cards(request):
    """
    Parents only. Generates ONE combined PDF with a page per linked child.
    """
    if request.user.role != 'parent':
        return redirect('dashboard')

    profiles = (
        StudentProfile.objects
        .filter(parent=request.user)
        .select_related('user')
        .order_by('user__first_name', 'user__username')
    )
    if not profiles.exists():
        messages.error(request, "You haven't linked any children yet.")
        return redirect('dashboard')

    children_data = []
    for student in profiles:
        attendance = Attendance.objects.filter(student=student)
        total = attendance.count()
        present = attendance.filter(status="present").count()
        att_pct = round((present / total * 100) if total else 0, 1)

        attempts_qs = QuizAttempt.objects.filter(
            student=student, completed_at__isnull=False
        ).order_by("-started_at")
        attempts_list = list(attempts_qs)
        avg_score = (
            round(sum(a.percentage() for a in attempts_list) / len(attempts_list), 1)
            if attempts_list else 0
        )

        children_data.append({
            'student': student,
            'att_pct': att_pct,
            'avg_score': avg_score,
            'attempts': attempts_list[:10],
        })

    return generate_combined_report_card(children_data)

# ================================================================
# TEACHER REVENUE DASHBOARD
# ================================================================
@login_required
def teacher_revenue_detail(request):
    if request.user.role != 'teacher':
        return redirect('dashboard')

    from payments.models import Payment
    from django.db.models import Sum

    teacher = request.user
    courses = Course.objects.filter(teacher=teacher)

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    paid_qs = Payment.objects.filter(course__in=courses, status="paid").select_related(
        'course', 'student__user', 'coupon'
    )

    # ---- Per-course stats ----
    course_rows = []
    lifetime_gross = Decimal("0")
    lifetime_teacher = Decimal("0")
    for course in courses:
        c_paid = paid_qs.filter(course=course)
        c_gross = c_paid.aggregate(s=Sum('amount'))['s'] or Decimal("0")
        rate = Decimal(course.revenue_share_percent) / Decimal(100)
        c_teacher = (c_gross * rate).quantize(Decimal("0.01"))
        lifetime_gross += c_gross
        lifetime_teacher += c_teacher
        course_rows.append({
            'course': course,
            'enrollments': c_paid.count(),
            'gross': c_gross,
            'teacher_earn': c_teacher,
            'platform_earn': (c_gross - c_teacher).quantize(Decimal("0.01")),
            'share_percent': course.revenue_share_percent,
        })
    course_rows.sort(key=lambda r: -r['teacher_earn'])

    # ---- Monthly (this month + this year) ----
    month_gross = Decimal("0")
    month_teacher = Decimal("0")
    year_gross = Decimal("0")
    year_teacher = Decimal("0")
    for p in paid_qs:
        rate = Decimal(p.course.revenue_share_percent) / Decimal(100)
        earn = p.amount * rate
        if p.created_at >= year_start:
            year_gross += p.amount
            year_teacher += earn
        if p.created_at >= month_start:
            month_gross += p.amount
            month_teacher += earn
    month_gross = month_gross.quantize(Decimal("0.01"))
    month_teacher = month_teacher.quantize(Decimal("0.01"))
    year_gross = year_gross.quantize(Decimal("0.01"))
    year_teacher = year_teacher.quantize(Decimal("0.01"))

    # ---- 12-month chart data ----
    month_starts = []
    cursor = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for _ in range(12):
        month_starts.append(cursor)
        if cursor.month == 1:
            cursor = cursor.replace(year=cursor.year - 1, month=12)
        else:
            cursor = cursor.replace(month=cursor.month - 1)
    month_starts.reverse()

    monthly_rows = []
    for i, start in enumerate(month_starts):
        end = month_starts[i + 1] if i + 1 < len(month_starts) else (now + timedelta(days=1))
        bucket = paid_qs.filter(created_at__gte=start, created_at__lt=end)
        b_gross = bucket.aggregate(s=Sum('amount'))['s'] or Decimal("0")
        b_teacher = Decimal("0")
        for p in bucket:
            b_teacher += p.amount * (Decimal(p.course.revenue_share_percent) / Decimal(100))
        b_teacher = b_teacher.quantize(Decimal("0.01"))
        monthly_rows.append({
            'label': start.strftime("%b %Y"),
            'gross': b_gross,
            'teacher_earn': b_teacher,
        })

    summary = {
        'lifetime_gross': lifetime_gross.quantize(Decimal("0.01")),
        'lifetime_teacher': lifetime_teacher.quantize(Decimal("0.01")),
        'lifetime_platform': (lifetime_gross - lifetime_teacher).quantize(Decimal("0.01")),
        'month_gross': month_gross,
        'month_teacher': month_teacher,
        'month_platform': (month_gross - month_teacher).quantize(Decimal("0.01")),
        'year_gross': year_gross,
        'year_teacher': year_teacher,
        'year_platform': (year_gross - year_teacher).quantize(Decimal("0.01")),
    }

    recent_payments = paid_qs.order_by('-created_at')[:20]
    recent_rows = []
    for p in recent_payments:
        rate = Decimal(p.course.revenue_share_percent) / Decimal(100)
        recent_rows.append({
            'payment': p,
            'teacher_earn': (p.amount * rate).quantize(Decimal("0.01")),
        })

    return render(request, "dashboard/teacher_revenue.html", {
        "courses": courses,
        "course_rows": course_rows,
        "monthly_rows": monthly_rows,
        "monthly_labels_json": json.dumps([r['label'] for r in monthly_rows]),
        "monthly_teacher_json": json.dumps([float(r['teacher_earn']) for r in monthly_rows]),
        "monthly_gross_json": json.dumps([float(r['gross']) for r in monthly_rows]),
        "summary": summary,
        "recent_rows": recent_rows,
    })


@login_required
def download_payout_statement(request):
    if request.user.role != 'teacher':
        return redirect('dashboard')

    from payments.models import Payment
    from django.db.models import Sum
    from .utils import generate_payout_statement

    teacher = request.user
    courses = Course.objects.filter(teacher=teacher)
    paid_qs = Payment.objects.filter(course__in=courses, status="paid").select_related('course')

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # Summary + course rows (same logic as view)
    course_rows = []
    lifetime_gross = Decimal("0")
    lifetime_teacher = Decimal("0")
    for course in courses:
        c_paid = paid_qs.filter(course=course)
        c_gross = c_paid.aggregate(s=Sum('amount'))['s'] or Decimal("0")
        rate = Decimal(course.revenue_share_percent) / Decimal(100)
        c_teacher = (c_gross * rate).quantize(Decimal("0.01"))
        lifetime_gross += c_gross
        lifetime_teacher += c_teacher
        course_rows.append({
            'course_title': course.title,
            'share_percent': course.revenue_share_percent,
            'enrollments': c_paid.count(),
            'gross': c_gross,
            'teacher_earn': c_teacher,
            'platform_earn': (c_gross - c_teacher).quantize(Decimal("0.01")),
        })
    course_rows.sort(key=lambda r: -r['teacher_earn'])

    month_gross = month_teacher = year_gross = year_teacher = Decimal("0")
    for p in paid_qs:
        rate = Decimal(p.course.revenue_share_percent) / Decimal(100)
        earn = p.amount * rate
        if p.created_at >= year_start:
            year_gross += p.amount
            year_teacher += earn
        if p.created_at >= month_start:
            month_gross += p.amount
            month_teacher += earn

    summary = {
        'lifetime_gross': lifetime_gross.quantize(Decimal("0.01")),
        'lifetime_teacher': lifetime_teacher.quantize(Decimal("0.01")),
        'lifetime_platform': (lifetime_gross - lifetime_teacher).quantize(Decimal("0.01")),
        'month_gross': month_gross.quantize(Decimal("0.01")),
        'month_teacher': month_teacher.quantize(Decimal("0.01")),
        'month_platform': (month_gross - month_teacher).quantize(Decimal("0.01")),
        'year_gross': year_gross.quantize(Decimal("0.01")),
        'year_teacher': year_teacher.quantize(Decimal("0.01")),
        'year_platform': (year_gross - year_teacher).quantize(Decimal("0.01")),
    }

    # 12-month rows (same as view)
    month_starts = []
    cursor = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for _ in range(12):
        month_starts.append(cursor)
        if cursor.month == 1:
            cursor = cursor.replace(year=cursor.year - 1, month=12)
        else:
            cursor = cursor.replace(month=cursor.month - 1)
    month_starts.reverse()

    monthly_rows = []
    for i, start in enumerate(month_starts):
        end = month_starts[i + 1] if i + 1 < len(month_starts) else (now + timedelta(days=1))
        bucket = paid_qs.filter(created_at__gte=start, created_at__lt=end)
        b_gross = bucket.aggregate(s=Sum('amount'))['s'] or Decimal("0")
        b_teacher = Decimal("0")
        for p in bucket:
            b_teacher += p.amount * (Decimal(p.course.revenue_share_percent) / Decimal(100))
        monthly_rows.append({
            'label': start.strftime("%b %Y"),
            'gross': b_gross.quantize(Decimal("0.01")),
            'teacher_earn': b_teacher.quantize(Decimal("0.01")),
        })

    return generate_payout_statement(
        teacher,
        period_label="All time (last 12 months detailed)",
        summary=summary,
        course_rows=course_rows,
        monthly_rows=monthly_rows,
    )