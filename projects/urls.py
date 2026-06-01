from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("projects/new/", views.project_create, name="project_create"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/delete/", views.project_delete, name="project_delete"),
    path("projects/<int:pk>/archive/", views.project_archive, name="project_archive"),
    path("tasks/add/<int:project_pk>/", views.task_add, name="task_add"),
    path("tasks/<int:pk>/toggle/", views.task_toggle, name="task_toggle"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),
    path("search/", views.search, name="search"),
]
