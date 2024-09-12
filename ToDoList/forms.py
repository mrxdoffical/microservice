from django import forms
from .models import ToDoItem

class ToDoItemForm(forms.ModelForm):
    class Meta:
        model = ToDoItem
        fields = ['title', 'description', 'completed']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Enter the title here...'}),
            'description': forms.Textarea(attrs={'class': 'form-control bg-dark text-white', 'rows': 3, 'placeholder': 'Enter your note here...'}),
            'completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }