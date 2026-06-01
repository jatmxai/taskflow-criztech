from django.contrib import admin
from .models import Project, Task


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "color", "archived", "created_at")
    list_filter = ("archived", "created_at")
    search_fields = ("name", "user__username")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "is_done", "priority", "due_date", "created_at")
    list_filter = ("is_done", "priority", "created_at")
    search_fields = ("title", "project__name")
