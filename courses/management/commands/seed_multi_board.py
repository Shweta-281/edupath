from django.core.management.base import BaseCommand
from accounts.models import User, StudentProfile, TeacherProfile
from courses.models import Course, Subject, Enrollment
import random

class Command(BaseCommand):
    help = 'Seeds CBSE and Maharashtra Board data for Classes 5-10'

    def handle(self, *args, **kwargs):
        self.stdout.write("⏳ Starting multi-board database seeding...")

        # Define Subjects based on the Board
        boards_data = {
            "CBSE": [
                {"name": "Mathematics", "icon": "bi-calculator"},
                {"name": "Science", "icon": "bi-lightbulb"},
                {"name": "English", "icon": "bi-book"},
                {"name": "Social Science", "icon": "bi-globe"},
                {"name": "Hindi", "icon": "bi-translate"},
                {"name": "Computer Science", "icon": "bi-laptop"},
            ],
            "Maharashtra Board": [
                {"name": "Mathematics", "icon": "bi-calculator"},
                {"name": "Science", "icon": "bi-lightbulb"},
                {"name": "English", "icon": "bi-book"},
                {"name": "History & Civics", "icon": "bi-bank"},
                {"name": "Geography", "icon": "bi-map"},
                {"name": "Marathi", "icon": "bi-translate"},
            ]
        }

        # Create generic teachers (we'll assign them to subjects)
        teacher_names = [
            ("Rajesh", "Verma"), ("Sunita", "Sharma"), ("Anil", "Deshmukh"), 
            ("Priya", "Patil"), ("Kavita", "Joshi"), ("Amit", "Singh")
        ]
        
        teachers = []
        for first, last in teacher_names:
            username = first.lower()
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': first, 'last_name': last, 'role': 'teacher', 'email': f"{username}@edupath.in"}
            )
            if created:
                user.set_password('pass12345')
                user.save()
                TeacherProfile.objects.get_or_create(user=user)
            teachers.append(user)

        student_count = 0
        course_count = 0
        enrollment_count = 0

        # Loop through Boards, Grades, and Subjects
        for board, subjects in boards_data.items():
            for grade in range(5, 11):
                for i, sub in enumerate(subjects):
                    subject_name = sub["name"]
                    icon = sub["icon"]
                    
                    # Create Subject
                    subject, _ = Subject.objects.get_or_create(
                        name=subject_name, 
                        grade=grade,
                        board=board,
                        defaults={'icon': icon}
                    )

                    # Create Course (Assign a random teacher to it)
                    teacher = random.choice(teachers)
                    course_title = f"{subject_name} - Class {grade} ({board})"
                    
                    course, created = Course.objects.get_or_create(
                        title=course_title,
                        subject=subject,
                        defaults={
                            'teacher': teacher,
                            'description': f"Complete {subject_name} curriculum for Class {grade} following the {board} syllabus.",
                            'price': random.choice([0, 499, 999]),
                            'is_free': random.choice([True, False])
                        }
                    )
                    if created:
                        course_count += 1

            # Create 5 Students per Board per Grade
            for i in range(1, 6):
                username = f"{board.split()[0].lower()}_student_{grade}_{i}" # e.g., cbse_student_10_1
                student_user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': f"Student {i}",
                        'last_name': f"{board} {grade}",
                        'role': 'student',
                        'email': f"{username}@edupath.in"
                    }
                )
                if created:
                    student_user.set_password('pass12345')
                    student_user.save()
                    student_profile, _ = StudentProfile.objects.get_or_create(
                        user=student_user, 
                        defaults={'grade': grade, 'board': board}
                    )
                    student_count += 1
                else:
                    student_profile = student_user.student_profile

                # Enroll the student in ALL courses matching THEIR board and THEIR grade
                board_grade_courses = Course.objects.filter(subject__grade=grade, subject__board=board)
                for gc in board_grade_courses:
                    enrollment, e_created = Enrollment.objects.get_or_create(
                        student=student_profile,
                        course=gc,
                        defaults={'is_active': True}
                    )
                    if e_created:
                        enrollment_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"🎉 Successfully seeded Multi-Board School!\n"
            f"📚 Courses Created: {course_count}\n"
            f"👨‍🎓 Students Created: {student_count}\n"
            f"✅ Enrollments Processed: {enrollment_count}"
        ))