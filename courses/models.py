from django.db import models
from decimal import Decimal
from accounts.models import User, StudentProfile
from django.conf import settings

BOARD_CHOICES = [('CBSE', 'CBSE'), ('Maharashtra Board', 'Maharashtra Board')] 


class Subject(models.Model):
    name = models.CharField(max_length=100)
    grade = models.IntegerField()
    board = models.CharField(max_length=50, choices=BOARD_CHOICES, default='CBSE')
    icon = models.CharField(max_length=50, default="bi-book")

    class Meta:
        unique_together = ("name", "grade", 'board')
        ordering = ["grade", "name"]

    def __str__(self):
        return f"{self.name} (Class {self.grade} - {self.board})"


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="courses")
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 limit_choices_to={"role": "teacher"})
    thumbnail = models.ImageField(upload_to="courses/", blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # NEW: per-course teacher revenue share (Option C — per-course override, global default = 70)
    revenue_share_percent = models.PositiveIntegerField(
        default=70,
        help_text="Teacher's share of each paid enrollment (%). Platform keeps the rest.",
    )

    def __str__(self):
        return self.title
    
    def get_progress(self, student_profile):
        from assessments.models import QuizAttempt, Submission

        total_lectures = Lecture.objects.filter(chapter__course=self).count()
        completed_lectures = LectureProgress.objects.filter(
            student=student_profile, lecture__chapter__course=self, is_completed=True
        ).count()

        total_quizzes = self.quizzes.count()
        completed_quizzes = QuizAttempt.objects.filter(
            student=student_profile, quiz__course=self, completed_at__isnull=False
        ).values('quiz').distinct().count()

        total_assignments = self.assignments.count()
        completed_assignments = Submission.objects.filter(
            student=student_profile, assignment__course=self
        ).values('assignment').distinct().count()

        total_tasks = total_lectures + total_quizzes + total_assignments
        completed_tasks = completed_lectures + completed_quizzes + completed_assignments

        if total_tasks == 0:
            return {'percentage': 0, 'is_completed': False}

        progress_pct = int((completed_tasks / total_tasks) * 100)
        
        return {
            'percentage': progress_pct,
            'completed_lectures': completed_lectures,
            'total_lectures': total_lectures,
            'completed_quizzes': completed_quizzes,
            'total_quizzes': total_quizzes,
            'completed_assignments': completed_assignments,
            'total_assignments': total_assignments,
            'is_completed': progress_pct >= 100
        }
        
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews.exists():
            return 0
        total = sum([r.rating for r in reviews])
        return round(total / reviews.count(), 1)

    # NEW: how much this teacher has earned from this course (lifetime)
    @property
    def teacher_earnings(self):
        from payments.models import Payment
        from django.db.models import Sum
        paid = (
            Payment.objects.filter(course=self, status="paid")
            .aggregate(s=Sum('amount'))['s'] or Decimal("0")
        )
        rate = Decimal(self.revenue_share_percent) / Decimal(100)
        return (paid * rate).quantize(Decimal("0.01"))

    # NEW: how much the platform keeps from this course (lifetime)
    @property
    def platform_earnings(self):
        from payments.models import Payment
        from django.db.models import Sum
        paid = (
            Payment.objects.filter(course=self, status="paid")
            .aggregate(s=Sum('amount'))['s'] or Decimal("0")
        )
        rate = Decimal(100 - self.revenue_share_percent) / Decimal(100)
        return (paid * rate).quantize(Decimal("0.01"))


class Chapter(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lecture(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="lectures")
    title = models.CharField(max_length=200)
    duration_minutes = models.IntegerField(default=10)
    video_url = models.URLField(blank=True, null=True, help_text="Paste a YouTube embed link here")
    content = models.TextField(blank=True, null=True, help_text="Optional text notes")

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("student", "course")


class LectureProgress(models.Model):
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE)
    lecture = models.ForeignKey('Lecture', on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now=True)
    watched_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('student', 'lecture')

    def __str__(self):
        return f"{self.student.user.username} - {self.lecture.title}"


class Discussion(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="discussions")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class DiscussionReply(models.Model):
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class CourseReview(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'student')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.user.username} - {self.course.title} ({self.rating} Stars)"


class Certificate(models.Model):
    student   = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE,
                                  related_name='certificates')
    course    = models.ForeignKey(Course, on_delete=models.CASCADE,
                                  related_name='certificates')
    serial    = models.CharField(max_length=40, unique=True, editable=False)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-issued_at']

    def save(self, *args, **kwargs):
        if not self.serial:
            import uuid
            self.serial = f"EP-{uuid.uuid4().hex[:8].upper()}-{self.course_id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.student.user.get_full_name() or self.student.user.username
        return f"{name} — {self.course.title} ({self.serial})"