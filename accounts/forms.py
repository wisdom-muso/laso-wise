from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

from .models import User


class DoctorRegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(DoctorRegistrationForm, self).__init__(*args, **kwargs)
        # Keep username field but make it optional
        if 'username' in self.fields:
            self.fields['username'].required = False
            self.fields['username'].help_text = "Optional. If left blank, a username will be generated for you."
            self.fields['username'].widget.attrs.update(
                {
                    "placeholder": "Enter username (optional)",
                }
            )
            
        self.fields["first_name"].label = "First name"
        self.fields["last_name"].label = "Last name"
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Confirm your password"

        self.fields["first_name"].widget.attrs.update(
            {
                "placeholder": "Enter first name",
                "required": True,
            }
        )
        self.fields["last_name"].widget.attrs.update(
            {
                "placeholder": "Enter last name",
                "required": True,
            }
        )
        self.fields["email"].widget.attrs.update(
            {
                "placeholder": "Enter email",
            }
        )
        self.fields["password1"].widget.attrs.update(
            {
                "placeholder": "Enter password",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "placeholder": "Confirm your password",
            }
        )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        ]
        error_messages = {
            "first_name": {
                "required": "First name is required",
                "max_length": "Name is too long",
            },
            "last_name": {
                "required": "Last name is required",
                "max_length": "Last Name is too long",
            },
        }

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.role = "doctor"
        # Note: We don't save here as the view will handle username generation and saving
        return user


class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "password1",
            "password2",
        ]

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.role = "patient"
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.fields["username"].widget.attrs.update(
            {"placeholder": "Enter Username"}
        )
        self.fields["password"].widget.attrs.update(
            {"placeholder": "Enter Password"}
        )

    def clean(self, *args, **kwargs):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if password and password:
            self.user = authenticate(username=username, password=password)

            if self.user is None:
                raise forms.ValidationError("Username or password is incorrect.")
            if not self.user.check_password(password):
                raise forms.ValidationError("Username or password is incorrect.")
            if not self.user.is_active:
                raise forms.ValidationError("User is not active.")

        return super(UserLoginForm, self).clean(*args, **kwargs)

    def get_user(self):
        return self.user
