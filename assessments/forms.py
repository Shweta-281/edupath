from django import forms
from .models import Quiz, Assignment, Submission
from courses.models import Course

# ==========================================
# EXISTING: QUIZ CREATION FORM
# ==========================================
class QuizCreateForm(forms.ModelForm):
    num_questions = forms.IntegerField(
        min_value=3, max_value=20, initial=5,
        help_text="How many questions to auto-generate (3–20)",
        widget=forms.NumberInput(attrs={"class": "form-input"}),
    )

    class Meta:
        model = Quiz
        fields = ["course", "title", "duration_minutes"]
        widgets = {
            "course": forms.Select(attrs={"class": "form-input"}),
            "title": forms.TextInput(attrs={"class": "form-input",
                                            "placeholder": "e.g. Algebra Quiz 2"}),
            "duration_minutes": forms.NumberInput(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Show ALL courses from Class 6 to 10
        self.fields["course"].queryset = Course.objects.filter(
            subject__grade__gte=6, 
            subject__grade__lte=10
        ).order_by('subject__grade', 'title')
        
        # Add a nice label for the dropdown
        self.fields["course"].label_from_instance = lambda obj: f"Class {obj.subject.grade} - {obj.subject.name}: {obj.title}"


# ==========================================
# NEW: ASSIGNMENT WORKFLOW FORMS
# ==========================================
class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'due_date', 'attachment']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Science Project Phase 1'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Provide instructions for the students...'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'attachment': forms.FileInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply the same Class 6-10 filtering for assignments
        self.fields["course"].queryset = Course.objects.filter(
            subject__grade__gte=6, 
            subject__grade__lte=10
        ).order_by('subject__grade', 'title')
        self.fields["course"].label_from_instance = lambda obj: f"Class {obj.subject.grade} - {obj.subject.name}: {obj.title}"


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['submitted_file']
        widgets = {
            'submitted_file': forms.FileInput(attrs={'class': 'form-input'}),
        }


class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['grade', 'feedback']
        widgets = {
            'grade': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., A, B+, 85/100'}),
            'feedback': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Write your feedback here...'}),
        }