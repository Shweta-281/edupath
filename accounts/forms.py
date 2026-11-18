from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from .models import User, StudentProfile, TeacherProfile, Message

# Make sure you import BOARD_CHOICES
from .models import BOARD_CHOICES 

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        initial="student"
    )
    phone = forms.CharField(max_length=15, required=False)
    grade = forms.ChoiceField(
        choices=[(str(i), f"Class {i}") for i in range(5, 11)],
        required=False,
        help_text="Only for students"
    )
    board = forms.ChoiceField(
        choices=BOARD_CHOICES,
        required=False,
        help_text="Only for students"
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "phone",
            "role",
            "grade",
            "password1",
            "password2",
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.phone = self.cleaned_data.get("phone", "")
        user.role = self.cleaned_data["role"]
        
        if commit:
            user.save()
            if user.role == "student":
                grade = self.cleaned_data.get("grade") or 5
                board = self.cleaned_data.get("board") or "Maharashtra Board" # Default to Maharashtra
                
                # Save the profile with the board
                StudentProfile.objects.create(
                    user=user, 
                    grade=int(grade), 
                    board=board
                )
            elif user.role == "teacher":
                TeacherProfile.objects.create(user=user)
                
        return user
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        grade = cleaned_data.get("grade")

        if role == "student" and not grade:
            self.add_error("grade", "Please select your class.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.phone = self.cleaned_data.get("phone", "")
        user.role = self.cleaned_data["role"]
        
        if commit:
            user.save()
            # If they registered as a student, create StudentProfile
            if user.role == "student":
                grade = self.cleaned_data.get("grade") or 5
                board = self.cleaned_data.get("board") or "CBSE"
                StudentProfile.objects.create(user=user, grade=int(grade), board=board)
            
            # NEW: If they registered as a teacher, create TeacherProfile
            elif user.role == "teacher":
                TeacherProfile.objects.create(user=user)
                
        return user


# ==========================================
# NEW: DIRECT MESSAGING FORM
# ==========================================
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'recipient': forms.Select(attrs={'class': 'form-input'}),
            'subject': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter subject'}),
            'body': forms.Textarea(attrs={'class': 'form-input', 'rows': 5, 'placeholder': 'Type your message here...'}),
        }

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Only allow messaging Teachers, Students, and Parents (not admins)
        self.fields['recipient'].queryset = User.objects.exclude(role='admin').order_by('role', 'username')
        self.fields['recipient'].label_from_instance = lambda obj: f"{obj.get_full_name() or obj.username} ({obj.role.title()})"
        
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'