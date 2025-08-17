from django import forms

from accounts.models import User
from bookings.models import Prescription
from ckeditor.widgets import CKEditorWidget
from doctors.models import TimeRange


class DoctorProfileForm(forms.ModelForm):
    """
    Doctor profile update form with image upload
    """
    
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Upload JPG, PNG, or GIF. Max size: 5MB'
    )
    
    # Profile fields
    specialization = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Cardiology, General Medicine'
        })
    )
    experience = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Years of experience'
        })
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number'
        })
    )
    about = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Brief description about yourself'
        })
    )
    price_per_consultation = forms.DecimalField(
        required=False,
        max_digits=8,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Consultation fee'
        })
    )
    
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "avatar"]
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Check file size (5MB max)
            if avatar.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image file too large. Maximum size is 5MB.")
            
            # Check file type
            if not avatar.content_type.startswith('image/'):
                raise forms.ValidationError("Please upload a valid image file.")
        
        return avatar


class DoctorScheduleForm(forms.Form):
    """
    Doctor schedule management form
    """
    
    DAYS_CHOICES = [
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    ]
    
    # Dynamic fields will be added in the view
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add fields for each day
        for day_num, day_name in self.DAYS_CHOICES:
            # Checkbox to enable the day
            self.fields[f'day_{day_num}'] = forms.BooleanField(
                required=False,
                label=day_name,
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
            )
            
            # Time slots for the day (multiple slots allowed)
            for slot in range(3):  # Allow up to 3 time slots per day
                self.fields[f'start_time_{day_num}_{slot}'] = forms.TimeField(
                    required=False,
                    widget=forms.TimeInput(attrs={
                        'class': 'form-control',
                        'type': 'time'
                    })
                )
                self.fields[f'end_time_{day_num}_{slot}'] = forms.TimeField(
                    required=False,
                    widget=forms.TimeInput(attrs={
                        'class': 'form-control',
                        'type': 'time'
                    })
                )


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["symptoms", "diagnosis", "medications", "notes"]
        widgets = {
            "symptoms": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
            "diagnosis": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
            "medications": CKEditorWidget(config_name="default"),
            "notes": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
        }
