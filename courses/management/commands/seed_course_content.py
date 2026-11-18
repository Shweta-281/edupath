from django.core.management.base import BaseCommand
from courses.models import Course, Chapter, Lecture
from assessments.models import Assignment, Quiz, Question, Choice
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Populates all existing courses with chapters, lectures, quizzes, and assignments'

    def handle(self, *args, **kwargs):
        self.stdout.write("⏳ Populating course content...")
        
        courses = Course.objects.all()
        count = 0

        for course in courses:
            # Delete existing content to avoid duplicates if run multiple times
            course.chapters.all().delete()
            course.assignments.all().delete()
            course.quizzes.all().delete()

            # Create 3 Chapters
            for i in range(1, 4):
                chapter = Chapter.objects.create(
                    course=course, 
                    title=f"Chapter {i}: {'Basics' if i==1 else 'Core Concepts' if i==2 else 'Advanced Topics'}"
                )
                
                # Create 3 Lectures per chapter
                for j in range(1, 4):
                    Lecture.objects.create(
                        chapter=chapter,
                        title=f"Lecture {j}: Understanding the Fundamentals",
                        duration_minutes=random.randint(10, 45),
                        # You can add a youtube_url here if your model has it
                    )

                # Create 1 Quiz per chapter
                quiz = Quiz.objects.create(
                    course=course,
                    chapter=chapter,
                    title=f"Chapter {i} Assessment",
                    total_marks=10,
                    duration_minutes=10,
                    is_published=True
                )
                # Create 2 Questions for the Quiz
                for q_num in range(1, 3):
                    q = Question.objects.create(quiz=quiz, text=f"Practice Question {q_num} for Chapter {i}?", marks=5)
                    Choice.objects.create(question=q, text="The Correct Answer", is_correct=True)
                    Choice.objects.create(question=q, text="A Wrong Answer", is_correct=False)

                # Create 1 Assignment per chapter
                Assignment.objects.create(
                    course=course,
                    title=f"Chapter {i} Homework Assignment",
                    description=f"Please complete the exercises at the end of Chapter {i} and upload your work here.",
                    due_date=timezone.now() + timedelta(days=7)
                )

            count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Successfully populated {count} courses with full content!'))