from django import forms
from .models import MobileClinicRequest

class MobileClinicRequestForm(forms.ModelForm):
    requested_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Select your preferred date for the mobile clinic visit"
    )
    requested_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text="Select your preferred time for the mobile clinic visit"
    )
    
    class Meta:
        model = MobileClinicRequest
        fields = ['requested_date', 'requested_time', 'address', 'reason', 'notes']
        widgets = {
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
    def clean_requested_date(self):
        date = self.cleaned_data.get('requested_date')
        from django.utils import timezone
        if date < timezone.now().date():
            raise forms.ValidationError("You cannot select a date in the past.")
        return date