from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.template.loader import render_to_string

from django.db.models import Count, Q

from .models import Project, Task
from .forms import RegisterForm, ProjectForm, TaskForm


def register(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("index")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def index(request):
    projects = Project.objects.filter(user=request.user, archived=False)
    archived_projects = Project.objects.filter(user=request.user, archived=True)
    user_tasks = Task.objects.filter(project__user=request.user, project__archived=False)
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(is_done=True).count()
    overall_progress = (
        int(completed_tasks / total_tasks * 100) if total_tasks else 0
    )
    form = ProjectForm()
    return render(
        request,
        "projects/index.html",
        {
            "projects": projects,
            "archived_projects": archived_projects,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overall_progress": overall_progress,
            "form": form,
        },
    )


@login_required
@require_POST
def project_create(request):
    form = ProjectForm(request.POST)
    if form.is_valid():
        project = form.save(commit=False)
        project.user = request.user
        project.save()
        if request.headers.get("HX-Request"):
            html = render_to_string(
                "projects/_project_card.html",
                {"project": project},
                request=request,
            )
            response = HttpResponse(html)
            response["HX-Trigger"] = '{"showToast": {"message": "Project created!", "type": "success"}}'
            return response
        return redirect("index")
    if request.headers.get("HX-Request"):
        return HttpResponse(status=400)
    return redirect("index")


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    tasks = project.tasks.all()
    form = TaskForm()
    return render(
        request,
        "projects/detail.html",
        {"project": project, "tasks": tasks, "form": form},
    )


@login_required
@require_POST
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    project.delete()
    messages.success(request, "Project deleted.")
    return redirect("index")


@login_required
@require_POST
def project_archive(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    project.archived = not project.archived
    project.save()
    return redirect("index")


@login_required
@require_POST
def task_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.save()
        if request.headers.get("HX-Request"):
            html = render_to_string(
                "projects/_task_row.html",
                {"task": task, "project": project},
                request=request,
            )
            progress_html = render_to_string(
                "projects/_progress.html",
                {"project": project},
                request=request,
            )
            response = HttpResponse(html + progress_html)
            response["HX-Trigger"] = '{"showToast": {"message": "Task added!", "type": "success"}}'
            return response
        return redirect("project_detail", pk=project.pk)
    if request.headers.get("HX-Request"):
        return HttpResponse(status=400)
    return redirect("project_detail", pk=project.pk)


@login_required
@require_POST
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk, project__user=request.user)
    task.is_done = not task.is_done
    task.save()
    if request.headers.get("HX-Request"):
        html = render_to_string(
            "projects/_task_row.html",
            {"task": task, "project": task.project},
            request=request,
        )
        progress_html = render_to_string(
            "projects/_progress.html",
            {"project": task.project},
            request=request,
        )
        return HttpResponse(html + progress_html)
    return redirect("project_detail", pk=task.project.pk)


@login_required
@require_http_methods(["DELETE", "POST"])
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, project__user=request.user)
    project = task.project
    task.delete()
    if request.headers.get("HX-Request"):
        progress_html = render_to_string(
            "projects/_progress.html",
            {"project": project},
            request=request,
        )
        response = HttpResponse(progress_html)
        response["HX-Trigger"] = '{"showToast": {"message": "Task deleted", "type": "info"}}'
        return response
    return redirect("project_detail", pk=project.pk)


@login_required
def search(request):
    query = request.GET.get("q", "").strip()
    tasks = []
    if query:
        tasks = Task.objects.filter(
            project__user=request.user, title__icontains=query
        ).select_related("project")[:20]
    return render(request, "projects/_search.html", {"tasks": tasks, "query": query})
