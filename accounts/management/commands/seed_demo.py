"""
Seed demo data for EduPath.

Usage:
    python manage.py seed_demo            # add demo data (skips what exists)
    python manage.py seed_demo --reset    # wipe demo data, then re-seed

Demo logins (password for all: demo1234):
    Teacher : t_priya
    Student : s_aarav
    Parent  : p_nilesh
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User, StudentProfile, TeacherProfile, ParentProfile
from courses.models import (
    Subject, Course, Chapter, Lecture, Enrollment, LectureProgress,
    CourseReview, Certificate, Discussion, DiscussionReply,
)
from assessments.models import (
    Quiz, Question, Choice, QuizAttempt, StudentAnswer, Assignment, Submission,
)
from attendance.models import Attendance
from payments.models import Payment, Coupon
from liveclasses.models import LiveClass, LiveClassAttendance, ParentMeeting
from dashboard.models import Notification


DEMO_DOMAIN = "demo.edupath.in"
DEMO_PASSWORD = "demo1234"


# ================================================================
# STATIC DATA
# ================================================================
TEACHERS_DATA = [
    ("Priya", "Sharma", "Mathematics", "CBSE", 8,
     "Passionate about making math visual and intuitive. 8+ years in CBSE schools."),
    ("Rajesh", "Kumar", "Science", "CBSE", 12,
     "Physics & Chemistry specialist. Former HOD at a Delhi public school."),
    ("Anjali", "Deshmukh", "English", "Maharashtra Board", 6,
     "Literature lover, grammar nerd, and essay coach."),
    ("Vikram", "Patil", "Social Studies", "Maharashtra Board", 10,
     "History & Geography through story-telling."),
    ("Sneha", "Iyer", "Mathematics", "CBSE", 5,
     "IIT-B alumna. Teaches math via real-world problems."),
    ("Amit", "Joshi", "Science", "Maharashtra Board", 9,
     "Biology & environmental science specialist."),
    ("Kavita", "Reddy", "English", "CBSE", 7,
     "Debate coach. Focus on spoken and written English."),
    ("Suresh", "Nair", "Computer Science", "CBSE", 15,
     "Ex-Infosys. Python & web development fundamentals."),
]

PARENTS_DATA = [
    ("Nilesh", "Patel", "9876543210", "12, Shanti Nagar, Ahmedabad, Gujarat 380015"),
    ("Meera", "Menon", "9876543211", "45, Marine Drive, Kochi, Kerala 682031"),
    ("Sanjay", "Rao", "9876543212", "78, Jayanagar, Bangalore, Karnataka 560041"),
    ("Pooja", "Singh", "9876543213", "23, Gomti Nagar, Lucknow, UP 226010"),
    ("Rakesh", "Gupta", "9876543214", "56, Rajouri Garden, New Delhi 110027"),
    ("Fatima", "Khan", "9876543215", "89, Bandra West, Mumbai, Maharashtra 400050"),
    ("Sunil", "Mehta", "9876543216", "34, Vastrapur, Ahmedabad, Gujarat 380015"),
    ("Neha", "Verma", "9876543217", "67, Koregaon Park, Pune, Maharashtra 411001"),
    ("Manoj", "Kapoor", "9876543218", "12, Sector 18, Noida, UP 201301"),
    ("Radhika", "Sharma", "9876543219", "45, Salt Lake, Kolkata, WB 700091"),
    ("Prakash", "Joshi", "9876543220", "78, Aundh, Pune, Maharashtra 411007"),
    ("Nisha", "Nair", "9876543221", "23, Adyar, Chennai, Tamil Nadu 600020"),
]

# (first, last, grade, board, parent_index_or_None)
STUDENTS_DATA = [
    ("Aarav", "Patel", 8, "CBSE", 0),
    ("Diya", "Menon", 8, "CBSE", 1),
    ("Arjun", "Rao", 9, "CBSE", 2),
    ("Ananya", "Singh", 9, "CBSE", 3),
    ("Vivaan", "Gupta", 10, "CBSE", 4),
    ("Sara", "Khan", 10, "CBSE", 5),
    ("Rohan", "Mehta", 7, "CBSE", 6),
    ("Ishita", "Verma", 7, "Maharashtra Board", 7),
    ("Kabir", "Kapoor", 6, "CBSE", 8),
    ("Aadhya", "Sharma", 6, "Maharashtra Board", 9),
    ("Reyansh", "Joshi", 5, "CBSE", 10),
    ("Myra", "Nair", 5, "Maharashtra Board", 11),
    ("Aditya", "Kulkarni", 10, "Maharashtra Board", None),
    ("Saanvi", "Bhat", 9, "Maharashtra Board", None),
    ("Vihaan", "Patel", 10, "CBSE", 0),         # sibling of Aarav
]

# (grade, board, subject_name, teacher_idx, price, is_free, share_percent)
COURSES_DATA = [
    (8, "CBSE", "Mathematics", 0, 999, False, 70),
    (8, "CBSE", "Science", 1, 899, False, 70),
    (8, "CBSE", "English", 6, 0, True, 70),
    (9, "CBSE", "Mathematics", 4, 1299, False, 70),
    (9, "CBSE", "Science", 1, 1199, False, 70),
    (9, "Maharashtra Board", "Social Studies", 3, 799, False, 65),
    (10, "CBSE", "Mathematics", 0, 1499, False, 75),
    (10, "CBSE", "Science", 1, 1399, False, 70),
    (10, "CBSE", "English", 6, 0, True, 70),
    (10, "Maharashtra Board", "Mathematics", 5, 1499, False, 70),
    (7, "CBSE", "Mathematics", 4, 899, False, 70),
    (7, "Maharashtra Board", "English", 2, 0, True, 70),
    (6, "CBSE", "Science", 1, 799, False, 70),
    (6, "Maharashtra Board", "Mathematics", 5, 0, True, 70),
    (5, "CBSE", "Mathematics", 0, 699, False, 70),
    (5, "Maharashtra Board", "English", 2, 0, True, 70),
    (8, "CBSE", "Computer Science", 7, 999, False, 80),
]

SUBJECT_ICONS = {
    "Mathematics": "bi-calculator",
    "Science": "bi-flask",
    "English": "bi-book",
    "Social Studies": "bi-globe",
    "Computer Science": "bi-cpu",
}

QUESTION_BANK = {
    "Mathematics": [
        ("What is the value of √144?", "12", ["10", "11", "13"]),
        ("Solve: 2x + 5 = 17. x = ?", "6", ["5", "7", "8"]),
        ("Area of a square with side 5 cm?", "25 cm²", ["20 cm²", "30 cm²", "10 cm²"]),
        ("Which is a prime number?", "17", ["15", "21", "27"]),
        ("Angle sum of a triangle is:", "180°", ["90°", "270°", "360°"]),
    ],
    "Science": [
        ("Chemical formula of water?", "H₂O", ["CO₂", "NaCl", "O₂"]),
        ("Powerhouse of the cell?", "Mitochondria", ["Nucleus", "Ribosome", "Golgi"]),
        ("Force = mass × ______", "acceleration", ["velocity", "distance", "time"]),
        ("SI unit of power:", "Watt", ["Joule", "Newton", "Pascal"]),
        ("Plants make food via:", "Photosynthesis", ["Respiration", "Digestion", "Transpiration"]),
    ],
    "English": [
        ("She ___ to school every day.", "goes", ["go", "going", "gone"]),
        ("Which is a conjunction?", "because", ["quickly", "happy", "run"]),
        ("Past tense of 'write':", "wrote", ["writed", "written", "writes"]),
        ("Synonym of 'happy':", "joyful", ["sad", "angry", "tired"]),
        ("Identify the adverb: 'She sang beautifully.'", "beautifully", ["She", "sang", "song"]),
    ],
    "Social Studies": [
        ("Capital of India?", "New Delhi", ["Mumbai", "Kolkata", "Chennai"]),
        ("First Prime Minister of India?", "Jawaharlal Nehru",
         ["Mahatma Gandhi", "Sardar Patel", "B.R. Ambedkar"]),
        ("Longest river in India?", "Ganga", ["Yamuna", "Brahmaputra", "Godavari"]),
        ("Constitution adopted in:", "1950", ["1947", "1948", "1949"]),
        ("Largest state by area?", "Rajasthan", ["MP", "Maharashtra", "UP"]),
    ],
    "Computer Science": [
        ("Which is a programming language?", "Python", ["HTTP", "HTML", "FTP"]),
        ("CPU stands for:", "Central Processing Unit",
         ["Computer Personal Unit", "Central Program Unit", "Control Processing Unit"]),
        ("HTML is used for:", "web pages", ["databases", "networks", "OSes"]),
        ("Binary uses:", "0 and 1", ["0-9", "1 and 2", "A and B"]),
        ("Which is NOT an OS?", "Google Chrome", ["Windows", "Linux", "macOS"]),
    ],
}


# ================================================================
# COMMAND
# ================================================================
class Command(BaseCommand):
    help = "Seed demo data (teachers, students, parents, courses, quizzes, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo data before seeding",
        )

    def handle(self, *args, **options):
        random.seed(42)
        self.stdout.write(self.style.MIGRATE_HEADING("EduPath Demo Seeder"))

        if options["reset"]:
            self._reset()

        with transaction.atomic():
            teachers = self._create_teachers()
            parents  = self._create_parents()
            students = self._create_students(parents)
            subjects = self._create_subjects()
            courses  = self._create_courses(teachers, subjects)
            self._populate_courses(courses)
            self._enroll_students(students, courses)
            self._create_payments(students, courses)
            self._create_attendance(students, courses)
            self._create_live_classes(courses)
            self._create_reviews(students, courses)
            self._create_discussions(courses, students, teachers)
            self._force_completions(students, courses)
            self._create_meetings(parents, teachers)
            self._create_notifications(students, teachers, parents)
            self._create_coupons()

        self._print_summary()

    # ---------- RESET ----------
    def _reset(self):
        self.stdout.write("  Deleting existing demo data...")
        demo_subject_ids = list(
            Subject.objects.filter(
                courses__teacher__email__endswith=DEMO_DOMAIN
            ).values_list("id", flat=True).distinct()
        )
        Course.objects.filter(teacher__email__endswith=DEMO_DOMAIN).delete()
        User.objects.filter(email__endswith=DEMO_DOMAIN).delete()
        Coupon.objects.filter(code__startswith="DEMO").delete()
        Subject.objects.filter(id__in=demo_subject_ids, courses__isnull=True).delete()
        self.stdout.write(self.style.WARNING("  ✓ Demo data wiped"))

    # ---------- HELPERS ----------
    def _ensure_user(self, username, email, role, first, last):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "role": role,
                       "first_name": first, "last_name": last},
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user, created

    # ---------- CREATORS ----------
    def _create_teachers(self):
        out = []
        for idx, (first, last, subject, board, exp, bio) in enumerate(TEACHERS_DATA):
            username = f"t_{first.lower()}"
            email = f"teacher.{first.lower()}@{DEMO_DOMAIN}"
            user, created = self._ensure_user(username, email, "teacher", first, last)
            if created:
                TeacherProfile.objects.create(
                    user=user,
                    subjects=f"{subject} ({board})",
                    bio=bio,
                    experience_years=exp,
                )
            out.append(user)
        self.stdout.write(f"  ✓ {len(out)} teachers")
        return out

    def _create_parents(self):
        out = []
        for idx, (first, last, phone, address) in enumerate(PARENTS_DATA):
            username = f"p_{first.lower()}"
            email = f"parent.{first.lower()}@{DEMO_DOMAIN}"
            user, created = self._ensure_user(username, email, "parent", first, last)
            if created:
                user.phone = phone
                user.save()
                ParentProfile.objects.create(user=user, address=address)
            out.append(user)
        self.stdout.write(f"  ✓ {len(out)} parents")
        return out

    def _create_students(self, parents):
        out = []
        for first, last, grade, board, parent_idx in STUDENTS_DATA:
            username = f"s_{first.lower()}"
            email = f"student.{first.lower()}@{DEMO_DOMAIN}"
            user, created = self._ensure_user(username, email, "student", first, last)
            if created:
                parent = parents[parent_idx] if parent_idx is not None else None
                StudentProfile.objects.create(
                    user=user,
                    grade=grade,
                    board=board,
                    parent=parent,
                    xp_points=random.randint(0, 850),
                )
            out.append(user.student_profile)
        self.stdout.write(f"  ✓ {len(out)} students")
        return out

    def _create_subjects(self):
        out = {}
        for grade, board, name, *_ in COURSES_DATA:
            key = (name, grade, board)
            if key in out:
                continue
            subject, _ = Subject.objects.get_or_create(
                name=name, grade=grade, board=board,
                defaults={"icon": SUBJECT_ICONS.get(name, "bi-book")},
            )
            out[key] = subject
        self.stdout.write(f"  ✓ {len(out)} subjects")
        return out

    def _create_courses(self, teachers, subjects):
        out = []
        for grade, board, name, t_idx, price, is_free, share in COURSES_DATA:
            subject = subjects[(name, grade, board)]
            teacher = teachers[t_idx]
            title = f"Class {grade} {name} ({board})"
            course, created = Course.objects.get_or_create(
                title=title,
                defaults={
                    "description": (
                        f"Complete {name} course for Class {grade} {board} students. "
                        "Covers the full syllabus with video lectures, quizzes, and "
                        "assignments. Includes live doubt-clearing sessions and "
                        "a certificate on completion."
                    ),
                    "subject": subject,
                    "teacher": teacher,
                    "price": Decimal(price),
                    "is_free": is_free,
                    "revenue_share_percent": share,
                },
            )
            out.append(course)
        self.stdout.write(f"  ✓ {len(out)} courses")
        return out

    def _populate_courses(self, courses):
        """Add chapters, lectures, quizzes, and assignments to each course."""
        total_lectures = total_quizzes = total_assignments = 0
        for course in courses:
            subj = course.subject.name
            for ch_order, ch_title in enumerate(["Introduction", "Core Concepts"], start=1):
                chapter, _ = Chapter.objects.get_or_create(
                    course=course, title=f"Chapter {ch_order}: {ch_title}",
                    defaults={"order": ch_order},
                )
                for lec_order in range(1, 4):
                    lec, created = Lecture.objects.get_or_create(
                        chapter=chapter,
                        title=f"{ch_title} - Lesson {lec_order}",
                        defaults={
                            "duration_minutes": random.randint(8, 20),
                            "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
                            "content": (
                                f"In this lesson we cover the fundamentals of "
                                f"{subj} as they relate to {ch_title.lower()}. "
                                "Watch the video, take notes, then attempt the quiz "
                                "at the end of the chapter."
                            ),
                        },
                    )
                    if created:
                        total_lectures += 1

            # one quiz per course
            quiz, q_created = Quiz.objects.get_or_create(
                course=course, title=f"{subj} - Chapter Test",
                defaults={"duration_minutes": 20, "is_published": True},
            )
            if q_created:
                bank = QUESTION_BANK.get(subj, QUESTION_BANK["Mathematics"])
                total_marks = 0
                for q_text, correct, wrongs in bank:
                    q = Question.objects.create(quiz=quiz, text=q_text, marks=2)
                    total_marks += 2
                    all_opts = [(correct, True)] + [(w, False) for w in wrongs]
                    random.shuffle(all_opts)
                    for opt_text, is_correct in all_opts:
                        Choice.objects.create(
                            question=q, text=opt_text, is_correct=is_correct,
                        )
                quiz.total_marks = total_marks
                quiz.save(update_fields=["total_marks"])
                total_quizzes += 1

            # one assignment per course
            _, a_created = Assignment.objects.get_or_create(
                course=course, title=f"{subj} - Homework 1",
                defaults={
                    "description": (
                        f"Complete all exercises from the first two chapters of {subj}. "
                        "Submit a scanned PDF of your handwritten work."
                    ),
                    "due_date": timezone.now() + timedelta(days=random.randint(3, 14)),
                },
            )
            if a_created:
                total_assignments += 1

        self.stdout.write(
            f"  ✓ {total_lectures} lectures, {total_quizzes} quizzes, "
            f"{total_assignments} assignments"
        )

    def _enroll_students(self, students, courses):
        total = 0
        for student in students:
            # Candidates = courses matching student's grade + board (up to 4)
            candidates = [
                c for c in courses
                if c.subject.grade == student.grade and c.subject.board == student.board
            ]
            if not candidates:
                continue
            k = random.randint(min(2, len(candidates)), min(4, len(candidates)))
            for course in random.sample(candidates, k=k):
                _, created = Enrollment.objects.get_or_create(
                    student=student, course=course,
                )
                if created:
                    total += 1
                    # backdate the enrollment
                    Enrollment.objects.filter(
                        student=student, course=course
                    ).update(
                        enrolled_at=timezone.now() - timedelta(
                            days=random.randint(5, 90)
                        )
                    )
        self.stdout.write(f"  ✓ {total} enrollments")

    def _create_payments(self, students, courses):
        count = 0
        for student in students:
            enrollments = Enrollment.objects.filter(student=student).select_related("course")
            for e in enrollments:
                course = e.course
                if Payment.objects.filter(student=student, course=course).exists():
                    continue
                amount = Decimal("0") if course.is_free else course.price
                method = "mock" if course.is_free else random.choice(
                    ["upi", "card", "netbanking", "wallet"]
                )
                payment = Payment.objects.create(
                    student=student,
                    course=course,
                    amount=amount,
                    method=method,
                    status="paid",
                    razorpay_payment_id=f"MOCK_{random.randint(100000, 999999)}",
                )
                # backdate
                Payment.objects.filter(pk=payment.pk).update(
                    created_at=timezone.now() - timedelta(
                        days=random.randint(5, 90)
                    )
                )
                count += 1
        self.stdout.write(f"  ✓ {count} payments")

    def _create_attendance(self, students, courses):
        count = 0
        for student in students:
            enrollments = Enrollment.objects.filter(student=student).select_related("course")
            for e in enrollments:
                course = e.course
                for days_ago in random.sample(range(1, 45), k=random.randint(6, 15)):
                    date = (timezone.now() - timedelta(days=days_ago)).date()
                    status = random.choices(
                        ["present", "absent", "late"],
                        weights=[80, 12, 8], k=1,
                    )[0]
                    _, created = Attendance.objects.get_or_create(
                        student=student, course=course, date=date,
                        defaults={"status": status, "marked_by": course.teacher},
                    )
                    if created:
                        count += 1
        self.stdout.write(f"  ✓ {count} attendance records")

    def _create_live_classes(self, courses):
        total = 0
        for course in courses:
            for i in range(2):
                offset_days = random.choice([-7, -3, 2, 5, 10])
                when = timezone.now() + timedelta(
                    days=offset_days, hours=random.randint(-2, 3)
                )
                title = f"Doubt Clearing Session {i+1}"
                if LiveClass.objects.filter(course=course, title=title).exists():
                    continue
                LiveClass.objects.create(
                    course=course,
                    title=title,
                    scheduled_at=when,
                    duration_minutes=60,
                    teacher=course.teacher,
                )
                total += 1
        self.stdout.write(f"  ✓ {total} live classes")

    def _create_reviews(self, students, courses):
        count = 0
        comments = [
            "Excellent course! Concepts explained very clearly.",
            "Loved the quizzes at the end of each chapter.",
            "The teacher is very responsive on the discussion forum.",
            "Good mix of theory and practice problems.",
            "Would recommend to anyone in this class.",
            "Content is well-structured. Wish there were more practice sets.",
            "Very helpful for exam preparation.",
        ]
        for course in courses:
            enrolled = Enrollment.objects.filter(course=course).select_related("student")
            for e in enrolled:
                if random.random() < 0.6:
                    _, created = CourseReview.objects.get_or_create(
                        course=course, student=e.student,
                        defaults={
                            "rating": random.choices(
                                [5, 4, 3, 2], weights=[50, 30, 15, 5], k=1
                            )[0],
                            "comment": random.choice(comments),
                        },
                    )
                    if created:
                        count += 1
        self.stdout.write(f"  ✓ {count} course reviews")

    def _create_discussions(self, courses, students, teachers):
        count = 0
        titles = [
            "Question about Chapter 2 exercise 5",
            "Doubts in the last quiz",
            "How to prepare for the upcoming test?",
            "Video not loading in lesson 3",
        ]
        for course in random.sample(courses, k=min(8, len(courses))):
            enrolled = list(
                Enrollment.objects.filter(course=course).select_related("student")
            )
            if not enrolled:
                continue
            for title in random.sample(titles, k=random.randint(1, 2)):
                if Discussion.objects.filter(course=course, title=title).exists():
                    continue
                student = random.choice(enrolled).student
                d = Discussion.objects.create(
                    course=course,
                    author=student.user,
                    title=title,
                    content=(
                        "Could someone please explain this in more detail? "
                        "I've re-watched the lecture but I'm still stuck."
                    ),
                )
                # teacher replies to about half
                if random.random() < 0.6:
                    DiscussionReply.objects.create(
                        discussion=d,
                        author=course.teacher,
                        content=(
                            "Great question! Check the notes on page 12 of the "
                            "lesson material — it walks through the exact step "
                            "you're missing. Let me know if that clears it up."
                        ),
                    )
                count += 1
        self.stdout.write(f"  ✓ {count} discussion threads")

    def _force_completions(self, students, courses):
        """Make a couple of students actually finish a course -> certificate."""
        completions = 0
        picks = [(students[0], "Class 8 Mathematics (CBSE)"),
                 (students[3], "Class 9 Science (CBSE)"),
                 (students[8], "Class 6 Science (CBSE)")]
        for student, course_title in picks:
            course = next((c for c in courses if c.title == course_title), None)
            if not course:
                continue
            # enroll if not already
            Enrollment.objects.get_or_create(student=student, course=course)
            # mark all lectures complete
            for lecture in Lecture.objects.filter(chapter__course=course):
                lp, _ = LectureProgress.objects.get_or_create(
                    student=student, lecture=lecture,
                )
                if not lp.is_completed:
                    lp.is_completed = True
                    lp.save()
            # attempt all quizzes with high score
            for quiz in Quiz.objects.filter(course=course):
                if not QuizAttempt.objects.filter(student=student, quiz=quiz).exists():
                    attempt = QuizAttempt.objects.create(
                        student=student, quiz=quiz,
                        score=int(quiz.total_marks * 0.9),
                        completed_at=timezone.now() - timedelta(days=3),
                    )
                    QuizAttempt.objects.filter(pk=attempt.pk).update(
                        started_at=timezone.now() - timedelta(days=3, hours=1)
                    )
            # submit all assignments
            for assignment in Assignment.objects.filter(course=course):
                if not Submission.objects.filter(
                    assignment=assignment, student=student
                ).exists():
                    Submission.objects.create(
                        assignment=assignment,
                        student=student,
                        submitted_file=SimpleUploadedFile(
                            f"submission_{student.id}.txt",
                            b"Demo assignment submission.",
                            content_type="text/plain",
                        ),
                        grade="A",
                        feedback="Well done!",
                    )
            # issue certificate
            Certificate.objects.get_or_create(student=student, course=course)
            completions += 1
        self.stdout.write(f"  ✓ {completions} course completions + certificates")

    def _create_meetings(self, parents, teachers):
        count = 0
        subjects = ["Mathematics", "Science", "Progress discussion",
                     "Attendance concern", "English improvement"]
        for i in range(4):
            parent = parents[i % len(parents)]
            teacher = teachers[i % len(teachers)]
            if ParentMeeting.objects.filter(
                parent=parent, teacher=teacher, status="pending"
            ).exists():
                continue
            ParentMeeting.objects.create(
                parent=parent,
                teacher=teacher,
                subject=random.choice(subjects),
                date=(timezone.now() + timedelta(days=random.randint(2, 10))).date(),
                time=(timezone.now() + timedelta(hours=random.randint(2, 8))).time(),
                status=random.choices(
                    ["pending", "approved", "completed"],
                    weights=[60, 30, 10], k=1,
                )[0],
            )
            count += 1
        self.stdout.write(f"  ✓ {count} parent meeting requests")

    def _create_notifications(self, students, teachers, parents):
        count = 0
        # notification to first 5 students
        for student in students[:5]:
            Notification.objects.create(
                recipient=student.user,
                title="🎉 Welcome to EduPath!",
                message=(
                    "Your account is ready. Explore your courses and start "
                    "learning today. Earn XP and climb the leaderboard!"
                ),
                link="/dashboard/",
            )
            count += 1
        # notification to first 3 teachers
        for teacher in teachers[:3]:
            Notification.objects.create(
                recipient=teacher,
                title="📊 Weekly class report is ready",
                message=(
                    "Your class analytics for this week are ready. "
                    "Check the dashboard for attendance trends."
                ),
                link="/dashboard/",
            )
            count += 1
        # notification to first 2 parents
        for parent in parents[:2]:
            Notification.objects.create(
                recipient=parent,
                title="👨‍👩‍👧 Your child's progress this week",
                message=(
                    "Tap to view attendance, quiz scores, and upcoming assignments."
                ),
                link="/dashboard/",
            )
            count += 1
        self.stdout.write(f"  ✓ {count} notifications")

    def _create_coupons(self):
        coupons = [
            ("DEMO10", 10, "Welcome offer — 10% off your first course"),
            ("DEMO25", 25, "Festive sale — 25% off"),
            ("DEMO50", 50, "Limited flash sale — 50% off"),
        ]
        count = 0
        for code, pct, _desc in coupons:
            _, created = Coupon.objects.get_or_create(
                code=code,
                defaults={
                    "discount_percent": pct,
                    "valid_until": timezone.now() + timedelta(days=90),
                    "is_active": True,
                    "max_uses": 100,
                },
            )
            if created:
                count += 1
        self.stdout.write(f"  ✓ {count} demo coupons")

    # ---------- SUMMARY ----------
    def _print_summary(self):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("━" * 60))
        self.stdout.write(self.style.SUCCESS("  ✓ Demo data seeded successfully"))
        self.stdout.write(self.style.SUCCESS("━" * 60))
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("  Login credentials (password: demo1234)"))
        self.stdout.write("")
        self.stdout.write("  👨‍🏫 Teacher :  t_priya     →  Priya Sharma (Math)")
        self.stdout.write("              t_rajesh    →  Rajesh Kumar (Science)")
        self.stdout.write("              t_suresh    →  Suresh Nair (Computer Science)")
        self.stdout.write("")
        self.stdout.write("  🎓 Student :  s_aarav     →  Aarav Patel (Class 8, has cert)")
        self.stdout.write("              s_ananya    →  Ananya Singh (Class 9, has cert)")
        self.stdout.write("              s_kabir     →  Kabir Kapoor (Class 6, has cert)")
        self.stdout.write("")
        self.stdout.write("  👨‍👩‍👧 Parent  :  p_nilesh    →  Nilesh Patel (2 children: Aarav, Vihaan)")
        self.stdout.write("              p_meera     →  Meera Menon (1 child: Diya)")
        self.stdout.write("")
        self.stdout.write("  🎟️  Coupons  :  DEMO10, DEMO25, DEMO50")
        self.stdout.write("")
        self.stdout.write("  To wipe and re-seed: python manage.py seed_demo --reset")
        self.stdout.write("")