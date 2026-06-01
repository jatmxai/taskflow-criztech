from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Project, Task


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "color")
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Project name",
                    "autofocus": True,
                }
            ),
            "color": forms.TextInput(
                attrs={
                    "type": "color",
                    "class": "h-10 w-16 rounded border border-gray-300 cursor-pointer",
                }
            ),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "priority", "due_date")
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Add a new task...",
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                }
            ),
        }
