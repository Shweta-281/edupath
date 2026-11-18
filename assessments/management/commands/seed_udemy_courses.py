from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from courses.models import Course, Chapter, Subject, User
from assessments.models import Assignment, Quiz, Question, Choice
from accounts.models import TeacherProfile

class Command(BaseCommand):
    help = 'Creates 5 complete courses with chapters, assignments, and quizzes'

    def handle(self, *args, **kwargs):
        # Get or create a teacher
        teacher_user, _ = User.objects.get_or_create(username='verma', defaults={'role': 'teacher'})
        teacher_user.set_password('pass12345')
        teacher_user.save()

        courses_data = [
            {"title": "Complete Python Bootcamp", "subject": "Computer Science", "grade": 10},
            {"title": "Advanced Mathematics", "subject": "Mathematics", "grade": 9},
            {"title": "Physics Fundamentals", "subject": "Physics", "grade": 10},
            {"title": "English Grammar Pro", "subject": "English", "grade": 8},
            {"title": "Chemistry Basics", "subject": "Chemistry", "grade": 9},
        ]

        for c_data in courses_data:
            subject, _ = Subject.objects.get_or_create(name=c_data["subject"], grade=c_data["grade"])
            
            course, created = Course.objects.get_or_create(
                title=c_data["title"],
                defaults={
                    'subject': subject,
                    'teacher': teacher_user,
                    'description': f"Master {c_data['title']} from scratch.",
                    'price': 499,
                    'is_free': False
                }
            )
            
            if created:
                # Create 2 Chapters
                for i in range(1, 3):
                    chapter = Chapter.objects.create(course=course, title=f"Chapter {i}: Basics")
                    
                    # Create 1 Quiz per chapter
                    quiz = Quiz.objects.create(
                        course=course, 
                        chapter=chapter, 
                        title=f"Chapter {i} Test",
                        total_marks=10,
                        duration_minutes=10,
                        is_published=True
                    )
                    # Create 2 Questions per quiz
                    for q_num in range(1, 3):
                        q = Question.objects.create(quiz=quiz, text=f"Question {q_num} for Chapter {i}?", marks=5)
                        Choice.objects.create(question=q, text="Correct Answer", is_correct=True)
                        Choice.objects.create(question=q, text="Wrong Answer 1", is_correct=False)
                        Choice.objects.create(question=q, text="Wrong Answer 2", is_correct=False)
                    
                    # Create 1 Assignment per chapter
                    Assignment.objects.create(
                        course=course,
                        title=f"Assignment {i}",
                        description=f"Please complete the practice exercise for Chapter {i}.",
                        due_date=timezone.now() + timedelta(days=7)
                    )

        self.stdout.write(self.style.SUCCESS('✅ Successfully seeded 5 Full Udemy-style Courses!'))