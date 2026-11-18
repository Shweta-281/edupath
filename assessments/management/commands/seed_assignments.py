from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from assessments.models import Assignment
from courses.models import Course

class Command(BaseCommand):
    help = 'Seeds 12 realistic dummy assignments into the database'

    def handle(self, *args, **kwargs):
        # Get all available courses
        courses = list(Course.objects.all())
        
        if not courses:
            self.stdout.write(self.style.ERROR('No courses found! Please create at least one course in the admin panel first.'))
            return

        # 12 Professional Assignment Templates
        assignments_data = [
            ("Algebra: Quadratic Equations Worksheet", "Solve the attached 20 quadratic equations. Show all your step-by-step working.", 7),
            ("Physics: Newton's Laws Lab Report", "Write a formal lab report on the experiment we did in class regarding Newton's Second Law.", 10),
            ("Life Processes: Plant Cell Diagram", "Draw a well-labeled diagram of a plant cell and upload a clear photo or PDF.", 5),
            ("English: Essay on 'My Favorite Book'", "Write a 300-word essay about your favorite book and explain why you recommend it to others.", 14),
            ("Computer Science: Python Basics Challenge", "Write a Python script that prints the first 10 Fibonacci numbers. Submit the .py file.", 4),
            ("Chemistry: Periodic Table Flashcards", "Create 10 digital flashcards for the first 10 elements of the periodic table.", 8),
            ("Environmental Science: Pollution Case Study", "Research a local pollution issue and write a 1-page case study on its impact.", 12),
            ("Grammar Practice: Tenses Worksheet", "Complete the attached worksheet on Past and Present Perfect tenses.", 3),
            ("History: Map Pointing - Indian Rivers", "Mark the major rivers of India on the blank map provided in the attachment.", 6),
            ("Geography: Climate Change Poster", "Design a digital poster raising awareness about climate change in your city.", 9),
            ("Math: Geometry Angles Worksheet", "Calculate the missing angles in the provided triangles. Show your calculations.", 2),
            ("Physics: Light and Reflection Diagram", "Draw ray diagrams for concave and convex mirrors showing image formation.", 11),
        ]

        count = 0
        for title, desc, days_offset in assignments_data:
            # Rotate through the courses you have in your database
            course = courses[count % len(courses)]
            
            # Check if it already exists to prevent duplicates if you run it twice
            if not Assignment.objects.filter(title=title, course=course).exists():
                due_date = timezone.now() + timedelta(days=days_offset)
                
                Assignment.objects.create(
                    course=course,
                    title=title,
                    description=desc,
                    due_date=due_date
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {count} assignments!'))