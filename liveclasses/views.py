from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from courses.models import Enrollment
from .models import LiveClass

import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import LiveClass, LiveClassAttendance
from courses.models import Enrollment


@login_required
def live_list(request):
    classes = LiveClass.objects.select_related("course").all()
    if request.user.role == "student":
        enrolled_ids = Enrollment.objects.filter(
            student=request.user.student_profile, is_active=True
        ).values_list("course_id", flat=True)
        classes = classes.filter(course_id__in=enrolled_ids)
    return render(request, "liveclasses/list.html", {"classes": classes})


@login_required
def join_class(request, pk):
    live = get_object_or_404(LiveClass, pk=pk)
    error = None
    if request.user.role == "student":
        if not Enrollment.objects.filter(
            student=request.user.student_profile,
            course=live.course,
            is_active=True,
        ).exists():
            error = "You must be enrolled in this course to join."
    elif request.user.role == "parent":
        error = "Parents cannot join live classes."
    return render(request, "liveclasses/join.html", {"live_class": live, "error": error})


# ================================================================
# LIVE-CLASS ATTENDANCE
# ================================================================
@login_required
def start_live_attendance(request, live_class_id):
    """Called once when the student loads the Jitsi room page."""
    if request.user.role != 'student':
        return JsonResponse({'ok': False, 'error': 'students only'}, status=403)

    live = get_object_or_404(LiveClass, id=live_class_id)
    student = request.user.student_profile

    if not Enrollment.objects.filter(
        student=student, course=live.course, is_active=True
    ).exists():
        return JsonResponse({'ok': False, 'error': 'not enrolled'}, status=403)

    record, created = LiveClassAttendance.objects.get_or_create(
        student=student, live_class=live,
    )
    # If they rejoin after leaving, clear left_at so duration resumes accumulating
    if record.left_at is not None:
        record.left_at = None
        record.save(update_fields=['left_at'])

    return JsonResponse({
        'ok': True,
        'created': created,
        'joined_at': record.joined_at.isoformat(),
    })


@login_required
def heartbeat_live_attendance(request, live_class_id):
    """JS pings this every 30s. Updates last_seen_at via auto_now."""
    if request.user.role != 'student':
        return JsonResponse({'ok': False}, status=403)

    student = request.user.student_profile
    record = LiveClassAttendance.objects.filter(
        student=student, live_class_id=live_class_id,
    ).first()
    if not record:
        return JsonResponse({'ok': False, 'error': 'no session'}, status=404)

    is_final = (
        request.POST.get('final') == '1'
        or request.GET.get('final') == '1'
    )

    if is_final:
        record.left_at = timezone.now()
        # Saving with both fields: last_seen_at (auto_now) + left_at
        record.save(update_fields=['last_seen_at', 'left_at'])
    else:
        record.save(update_fields=['last_seen_at'])

    return JsonResponse({
        'ok': True,
        'duration_seconds': record.duration_seconds,
        'attendance_percent': record.attendance_percent,
    })


@login_required
def live_class_attendance_report(request, live_class_id):
    """Teacher-facing report: who joined, for how long, present/absent."""
    live = get_object_or_404(
        LiveClass.objects.select_related('course', 'teacher'),
        id=live_class_id,
    )

    if request.user != live.teacher and request.user.role != 'admin':
        messages.error(request, "You can only view attendance for your own classes.")
        return redirect('dashboard')

    enrolled = (
        Enrollment.objects
        .filter(course=live.course, is_active=True)
        .select_related('student__user')
    )
    records = {
        r.student_id: r
        for r in LiveClassAttendance.objects
            .filter(live_class=live)
            .select_related('student__user')
    }

    rows = []
    present_count = 0
    for e in enrolled:
        rec = records.get(e.student_id)
        is_present = bool(rec and rec.is_present)
        if is_present:
            present_count += 1
        rows.append({
            'student': e.student,
            'record': rec,
            'duration_min': round(rec.duration_seconds / 60, 1) if rec else 0,
            'percent': rec.attendance_percent if rec else 0,
            'is_present': is_present,
        })

    rows.sort(key=lambda r: (
        not r['is_present'],
        -r['percent'],
        (r['student'].user.get_full_name() or r['student'].user.username).lower(),
    ))

    total = len(rows)
    present_pct = round((present_count / total * 100) if total else 0, 1)
    absent_count = total - present_count

    return render(request, 'liveclasses/attendance_report.html', {
        'live': live,
        'rows': rows,
        'total': total,
        'present_count': present_count,
        'absent_count': absent_count,          # ← new
        'present_pct': present_pct,
    })