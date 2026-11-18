from django.db import models
from django.contrib.auth.models import AbstractUser

GRADE_CHOICES = [(i, f"Class {i}") for i in range(5, 11)]
BOARD_CHOICES = [('CBSE', 'CBSE'), ('Maharashtra Board', 'Maharashtra Board')] 

class User(AbstractUser):                            # TABLE 1
    ROLE_CHOICES = [
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("parent", "Parent"),
        ("admin", "Admin"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="student")
    phone = models.CharField(max_length=15, blank=True)
    
    # NEW: Profile Picture
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class StudentProfile(models.Model):                  # TABLE 2
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    grade = models.IntegerField(choices=GRADE_CHOICES, default=5)
    # NEW: Board Field
    board = models.CharField(max_length=50, choices=BOARD_CHOICES, default='CBSE')
    parent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="children", limit_choices_to={"role": "parent"})
    enrollment_date = models.DateField(auto_now_add=True)
    
    # NEW: Gamification Field
    xp_points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - Class {self.grade}"
    
    # NEW: Level Calculation Logic
    @property
    def level_info(self):
        # Level 1 = 0-99 XP, Level 2 = 100-199 XP, etc.
        level = (self.xp_points // 100) + 1
        xp_in_current_level = self.xp_points % 100
        progress_pct = int((xp_in_current_level / 100) * 100)
        
        return {
            'level': level,
            'progress': progress_pct,
            'xp_next': 100 - xp_in_current_level,
            'total_xp': self.xp_points
        }

    # NEW: AI Risk Predictor Logic
    @property
    def risk_status(self):
        from attendance.models import Attendance
        from assessments.models import QuizAttempt
        
        # 1. Calculate Attendance Percentage
        attendances = Attendance.objects.filter(student=self)
        total_classes = attendances.count()
        
        if total_classes > 0:
            # 'present' or 'late' counts as attended
            attended = attendances.filter(status__in=['present', 'late']).count()
            att_pct = (attended / total_classes) * 100
        else:
            att_pct = 100 # Default if no data yet
            
        # 2. Calculate Quiz Average
        attempts = QuizAttempt.objects.filter(student=self, completed_at__isnull=False)
        if attempts.exists():
            # Calculate average of all quiz percentages
            total_pct = sum([a.percentage() for a in attempts])
            avg_score = total_pct / attempts.count()
        else:
            avg_score = 100 # Default if no data yet

        # 3. Apply Risk Rules
        if att_pct < 75 or avg_score < 40:
            return {'label': 'High Risk', 'color': '#b91c1c', 'bg': '#fee2e2', 'msg': 'Immediate attention needed. Scores or attendance are very low.'}
        elif att_pct < 85 or avg_score < 60:
            return {'label': 'Medium Risk', 'color': '#d97706', 'bg': '#fef3c7', 'msg': 'Keep an eye on upcoming quizzes and attendance.'}
        else:
            return {'label': 'Safe', 'color': '#15803d', 'bg': '#dcfce7', 'msg': 'Performing excellently! Keep it up.'}


class TeacherProfile(models.Model):                  # TABLE 3
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    subjects = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Teacher: {self.user.username}"


class ParentProfile(models.Model):                   # TABLE 4
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")
    address = models.TextField(blank=True)

    def __str__(self):
        return f"Parent: {self.user.username}"

# NEW: Audit Log Model
class AuditLog(models.Model):
    action = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    subject = models.CharField(max_length=255)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} to {self.recipient.username}: {self.subject}"