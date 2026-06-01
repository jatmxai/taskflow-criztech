from django.db import models
from django.contrib.auth.models import User


PRIORITY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]


class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=120)
    color = models.CharField(max_length=7, default="#3B82F6")
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def total_tasks(self):
        return self.tasks.count()

    @property
    def completed_tasks(self):
        return self.tasks.filter(is_done=True).count()

    @property
    def progress(self):
        total = self.total_tasks
        if total == 0:
            return 0
        return int((self.completed_tasks / total) * 100)

    @property
    def remaining_tasks(self):
        return self.total_tasks - self.completed_tasks


class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, default="medium", choices=PRIORITY_CHOICES)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_done", "-created_at"]

    def __str__(self):
        return self.title
