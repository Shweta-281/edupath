import uuid
from django.db import models
from django.utils import timezone
from courses.models import Course
from accounts.models import User, StudentProfile


class LiveClass(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="live_classes")
    title = models.CharField(max_length=200)
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    jitsi_room = models.CharField(max_length=100, unique=True, editable=False)
    recording_url = models.URLField(blank=True)

    class Meta:
        ordering = ["-scheduled_at"]

    def save(self, *args, **kwargs):
        if not self.jitsi_room:
            self.jitsi_room = f"edupath-{uuid.uuid4().hex[:10]}"
        super().save(*args, **kwargs)

    @property
    def ended_at(self):
        return self.scheduled_at + timezone.timedelta(minutes=self.duration_minutes)

    @property
    def is_live_now(self):
        now = timezone.now()
        return self.scheduled_at <= now <= self.ended_at

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class ParentMeeting(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),     # <-- added; your template already used 'rejected'
        ("completed", "Completed"),
    ]
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="meeting_requests")
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="teacher_meetings",
        limit_choices_to={"role": "teacher"},
    )
    subject = models.CharField(max_length=100, help_text="e.g. Mathematics")
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.parent.username} -> {self.teacher.username} on {self.date}"


# ================================================================
# NEW: Live-Class Attendance
# ================================================================
class LiveClassAttendance(models.Model):
    student    = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE,
        related_name="live_attendance",
    )
    live_class = models.ForeignKey(
        LiveClass, on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    joined_at    = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)   # bumped by heartbeat
    left_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "live_class")
        ordering = ["-joined_at"]

    # ---------- helpers ----------
    @property
    def duration_seconds(self):
        end = self.left_at or self.last_seen_at
        return max(0, int((end - self.joined_at).total_seconds()))

    @property
    def attendance_percent(self):
        required = self.live_class.duration_minutes * 60
        if not required:
            return 0
        return min(100, int((self.duration_seconds / required) * 100))

    @property
    def is_present(self):
        # Present = watched at least 50% of the scheduled duration
        return self.attendance_percent >= 50

    def __str__(self):
        return f"{self.student.user.username} → {self.live_class.title} ({self.attendance_percent}%)"