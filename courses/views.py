from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import (
    Course, Lecture, Enrollment, LectureProgress, CourseReview,
    Discussion, DiscussionReply, Certificate,
)
from .utils import generate_certificate
from .forms import ChapterForm, LectureForm


def course_list(request):
    courses = Course.objects.all()
    query = request.GET.get('q')
    if query:
        courses = courses.filter(title__icontains=query) | courses.filter(subject__name__icontains=query)
        courses = courses.distinct()

    if request.user.is_authenticated and request.user.role == 'student':
        student_profile = request.user.student_profile
        courses = courses.filter(subject__board=student_profile.board)
        grade_param = request.GET.get('grade')
        if grade_param == 'all':
            pass
        elif grade_param:
            courses = courses.filter(subject__grade=grade_param)
        else:
            courses = courses.filter(subject__grade=student_profile.grade)
    else:
        grade_param = request.GET.get('grade')
        if grade_param and grade_param != 'all':
            courses = courses.filter(subject__grade=grade_param)

    current_grade = request.GET.get(
        'grade',
        request.user.student_profile.grade
        if request.user.is_authenticated and request.user.role == 'student'
        else 'all'
    )

    return render(request, 'courses/list.html', {
        'courses': courses,
        'current_grade': str(current_grade),
        'search_query': query,
    })


def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    chapters = course.chapters.all().prefetch_related('lectures', 'quizzes')
    reviews = course.reviews.all().select_related('student__user')

    enrolled = False
    has_reviewed = False
    has_certificate = False
    progress = None

    if request.user.is_authenticated and request.user.role == 'student':
        student = request.user.student_profile
        enrolled = Enrollment.objects.filter(student=student, course=course, is_active=True).exists()
        has_reviewed = CourseReview.objects.filter(student=student, course=course).exists()
        has_certificate = Certificate.objects.filter(student=student, course=course).exists()
        if enrolled:
            progress = course.get_progress(student)

    if request.method == "POST" and enrolled and not has_reviewed:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating:
            CourseReview.objects.create(
                course=course, student=request.user.student_profile,
                rating=int(rating), comment=comment,
            )
            messages.success(request, "⭐ Thank you for your review!")
            return redirect('course_detail', pk=course.pk)

    return render(request, 'courses/detail.html', {
        'course': course,
        'chapters': chapters,
        'enrolled': enrolled,
        'reviews': reviews,
        'has_reviewed': has_reviewed,
        'has_certificate': has_certificate,
        'progress': progress,
    })


@login_required
def lecture_view(request, pk):
    lecture = get_object_or_404(
        Lecture.objects.select_related("chapter__course__subject"), pk=pk
    )
    course = lecture.chapter.course
    progress = None
    is_completed = False

    if request.user.role == "student":
        try:
            student = request.user.student_profile
        except AttributeError:
            messages.error(request, "Your student profile was not found. Please contact the administrator.")
            return redirect("course_detail", pk=course.pk)

        if not Enrollment.objects.filter(student=student, course=course, is_active=True).exists():
            messages.error(request, "Please enroll in this course to access its lectures.")
            return redirect("course_detail", pk=course.pk)

        progress, _ = LectureProgress.objects.get_or_create(student=student, lecture=lecture)
        is_completed = progress.is_completed

    elif request.user.role not in {"teacher", "admin"}:
        messages.error(request, "You are not authorized to access this lecture.")
        return redirect("course_detail", pk=course.pk)

    all_lectures = Lecture.objects.filter(chapter__course=course).order_by('chapter__id', 'id')

    return render(request, 'courses/lecture.html', {
        'lecture': lecture,
        'course': course,
        'progress': progress,
        'is_completed': is_completed,
        'all_lectures': all_lectures,
    })


@login_required
def mark_lecture_complete(request, pk):
    lecture = get_object_or_404(Lecture, pk=pk)
    student_profile = request.user.student_profile

    progress, created = LectureProgress.objects.get_or_create(
        student=student_profile, lecture=lecture,
    )
    # Only award XP the first time
    if not progress.is_completed:
        progress.is_completed = True
        progress.save()
        student_profile.xp_points += 10
        student_profile.save()
        messages.success(request, "✅ Lecture marked as complete! +10 XP")
    else:
        messages.info(request, "This lecture was already marked complete.")

    next_lecture = Lecture.objects.filter(
        chapter__course=lecture.chapter.course, id__gt=lecture.id
    ).order_by('id').first()

    if next_lecture:
        return redirect('lecture_view', pk=next_lecture.pk)
    return redirect('course_detail', pk=lecture.chapter.course.pk)


@login_required
def discussion_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    discussions = course.discussions.all()

    if request.method == "POST":
        title = request.POST.get('title')
        content = request.POST.get('content')
        if title and content:
            Discussion.objects.create(
                course=course, author=request.user, title=title, content=content,
            )
            messages.success(request, "✅ Discussion posted!")
            return redirect('discussion_list', course_id=course.id)

    return render(request, 'courses/discussion_list.html', {
        'course': course, 'discussions': discussions,
    })


@login_required
def discussion_detail(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id)
    if request.method == "POST":
        content = request.POST.get('content')
        if content:
            DiscussionReply.objects.create(
                discussion=discussion, author=request.user, content=content,
            )
            return redirect('discussion_detail', discussion_id=discussion.id)
    return render(request, 'courses/discussion_detail.html', {'discussion': discussion})


# ================================================================
# CERTIFICATE VIEWS
# ================================================================
@login_required
def download_certificate(request, course_id):
    """Issue (first time) or re-download the certificate PDF for a completed course."""
    course = get_object_or_404(Course, id=course_id)

    if request.user.role != 'student':
        messages.error(request, "Only students can download certificates.")
        return redirect('dashboard')

    try:
        student = request.user.student_profile
    except AttributeError:
        messages.error(request, "Student profile not found.")
        return redirect('course_detail', pk=course.pk)

    progress = course.get_progress(student)
    if not progress or not progress.get('is_completed'):
        messages.error(request, "You must complete 100% of this course to earn a certificate.")
        return redirect('course_detail', pk=course.pk)

    certificate, _ = Certificate.objects.get_or_create(student=student, course=course)

    student_name = request.user.get_full_name() or request.user.username
    teacher_name = (
        course.teacher.get_full_name() or course.teacher.username
        if course.teacher else "EduPath Instructor"
    )

    return generate_certificate(
        student_name,
        course.title,
        teacher_name,
        serial=certificate.serial,
        issued_on=certificate.issued_at.date(),
    )


@login_required
def my_certificates(request):
    """List all certificates a student has earned."""
    if request.user.role != 'student':
        messages.error(request, "Only students have certificates.")
        return redirect('dashboard')

    try:
        student = request.user.student_profile
    except AttributeError:
        return redirect('dashboard')

    certs = (
        Certificate.objects
        .filter(student=student)
        .select_related('course', 'course__subject', 'course__teacher')
    )
    return render(request, 'courses/my_certificates.html', {'certificates': certs})


def verify_certificate(request, serial):
    """Public verification page — no login required."""
    cert = (
        Certificate.objects
        .select_related('student__user', 'course', 'course__teacher')
        .filter(serial=serial)
        .first()
    )
    return render(request, 'courses/certificate_verify.html', {
        'cert': cert,
        'is_valid': cert is not None,
        'serial': serial,
    })


@login_required
def teacher_manage_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, "You do not have permission to manage this course.")
        return redirect('dashboard')

    chapters = course.chapters.all().prefetch_related('lectures')

    if request.method == "POST":
        if 'add_chapter' in request.POST:
            chapter_form = ChapterForm(request.POST)
            if chapter_form.is_valid():
                chapter = chapter_form.save(commit=False)
                chapter.course = course
                chapter.save()
                messages.success(request, "✅ Chapter added successfully!")
                return redirect('teacher_manage_course', pk=course.pk)
        elif 'add_lecture' in request.POST:
            lecture_form = LectureForm(request.POST)
            chapter_id = request.POST.get('chapter_id')
            if lecture_form.is_valid() and chapter_id:
                lecture = lecture_form.save(commit=False)
                lecture.chapter_id = chapter_id
                lecture.save()
                messages.success(request, "✅ Lecture added successfully!")
                return redirect('teacher_manage_course', pk=course.pk)
    else:
        chapter_form = ChapterForm()
        lecture_form = LectureForm()

    return render(request, 'courses/manage_course.html', {
        'course': course, 'chapters': chapters,
        'chapter_form': chapter_form, 'lecture_form': lecture_form,
    })