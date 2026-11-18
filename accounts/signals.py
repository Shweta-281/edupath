# accounts/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import AuditLog

# 🔥 FIX: These must come from assessments.models and courses.models, NOT .models!
from assessments.models import Assignment, Quiz, Submission
from courses.models import Enrollment
from dashboard.models import Notification

# ==========================================
# 1. AUDIT LOG SIGNALS
# ==========================================
@receiver(post_save, sender=Enrollment)
def log_enrollment(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            user=instance.student.user if hasattr(instance, 'student') else None,
            action="New Enrollment",
            details=f"Enrolled in course: {instance.course.title}"
        )

@receiver(pre_save, sender=Submission)
def log_grade_change(sender, instance, **kwargs):
    if instance.pk:
        old_sub = sender.objects.get(pk=instance.pk)
        if old_sub.grade != instance.grade:
            AuditLog.objects.create(
                user=instance.assignment.course.teacher,
                action="Grade Updated",
                details=f"Updated grade for {instance.student.user.username} to '{instance.grade}' in {instance.assignment.title}"
            )

# ==========================================
# 2. NOTIFICATION SIGNALS
# ==========================================
@receiver(post_save, sender=Assignment)
def notify_students_new_assignment(sender, instance, created, **kwargs):
    if created:
        enrollments = Enrollment.objects.filter(course=instance.course, is_active=True)
        notifications = []
        for e in enrollments:
            notifications.append(
                Notification(
                    recipient=e.student.user,
                    title="📝 New Assignment Posted",
                    message=f"A new assignment '{instance.title}' has been posted in {instance.course.title}.",
                    link="/quiz/assignments/student/"
                )
            )
        Notification.objects.bulk_create(notifications)

@receiver(post_save, sender=Quiz)
def notify_students_new_quiz(sender, instance, created, **kwargs):
    if created and instance.is_published:
        enrollments = Enrollment.objects.filter(course=instance.course, is_active=True)
        notifications = []
        for e in enrollments:
            notifications.append(
                Notification(
                    recipient=e.student.user,
                    title="🧠 New Quiz Available",
                    message=f"A new quiz '{instance.title}' is ready to take in {instance.course.title}.",
                    link="/quiz/"
                )
            )
        Notification.objects.bulk_create(notifications)

@receiver(post_save, sender=Submission)
def notify_student_graded(sender, instance, created, **kwargs):
    if not created and instance.grade:
        Notification.objects.create(
            recipient=instance.student.user,
            title="🎉 Assignment Graded",
            message=f"Your submission for '{instance.assignment.title}' has been graded. You scored: {instance.grade}",
            link="/quiz/assignments/student/"
        )