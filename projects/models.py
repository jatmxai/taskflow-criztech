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


class EmailPreference(models.Model):
    """Per-user toggles for which events trigger an email notification."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="email_prefs"
    )
    enabled = models.BooleanField(default=True)
    project_created = models.BooleanField(default=True)
    project_deleted = models.BooleanField(default=True)
    task_created = models.BooleanField(default=False)
    task_completed = models.BooleanField(default=True)
    task_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"EmailPrefs<{self.user.username}>"

    @classmethod
    def for_user(cls, user):
        prefs, _ = cls.objects.get_or_create(user=user)
        return prefs


class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="subtasks"
    )
    title = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, default="medium", choices=PRIORITY_CHOICES)
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_done", "order", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def subtask_progress(self):
        total = self.subtasks.count()
        if not total:
            return None
        done = self.subtasks.filter(is_done=True).count()
        return {"total": total, "done": done, "percent": int(done / total * 100)}
