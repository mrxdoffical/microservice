from django.db import models
from django.contrib.auth.models import User

class ToDoItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # Replace 1 with the ID of your default user
    title = models.CharField(max_length=100, default="Untitled")  # New title field
    description = models.TextField(default="no description provided")
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}: {self.description[:50]}"  # Display the title and the first 50 characters of the description