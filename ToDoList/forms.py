from django import forms
from .models import ToDoItem

class ToDoItemForm(forms.ModelForm):
    class Meta:
        model = ToDoItem
        fields = ['description', 'completed']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control bg-dark text-white', 'rows': 3, 'placeholder': 'Enter your note here...'}),
            'completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }