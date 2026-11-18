from django import forms
from .models import Chapter, Lecture

class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Chapter 1: Introduction to Physics'}),
        }

class LectureForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = ['title', 'duration_minutes', 'video_url', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Lecture 1: Newton\'s Laws'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-input'}),
            'video_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://www.youtube.com/embed/...'}),
            'content': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }