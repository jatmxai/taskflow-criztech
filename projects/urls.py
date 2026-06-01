from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("today/", views.today_view, name="today"),
    path("settings/", views.settings_view, name="settings"),
    path("projects/new/", views.project_create, name="project_create"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/delete/", views.project_delete, name="project_delete"),
    path("projects/<int:pk>/archive/", views.project_archive, name="project_archive"),
    path("tasks/add/<int:project_pk>/", views.task_add, name="task_add"),
    path("tasks/<int:pk>/toggle/", views.task_toggle, name="task_toggle"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),
    path("tasks/reorder/", views.task_reorder, name="task_reorder"),
    path("subtasks/add/<int:parent_pk>/", views.subtask_add, name="subtask_add"),
    path("subtasks/<int:pk>/toggle/", views.subtask_toggle, name="subtask_toggle"),
    path("subtasks/<int:pk>/delete/", views.subtask_delete, name="subtask_delete"),
    path("search/", views.search, name="search"),
    path("palette/", views.palette, name="palette"),
]
