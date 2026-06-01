import json
from datetime import date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from django.template.loader import render_to_string
from django.db.models import Count, Q

from .models import Project, Task, EmailPreference
from .forms import RegisterForm, ProjectForm, TaskForm
from .parser import parse_task_input
from .email_utils import notify


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


def _compute_streak(user):
    """Consecutive day streak ending today or yesterday."""
    completed = (
        Task.objects.filter(project__user=user, completed_at__isnull=False)
        .dates("completed_at", "day", order="DESC")
    )
    days = list(completed)
    if not days:
        return 0
    today = timezone.localdate()
    if days[0] not in (today, today - timedelta(days=1)):
        return 0
    streak = 1
    for i in range(1, len(days)):
        if days[i] == days[i - 1] - timedelta(days=1):
            streak += 1
        else:
            break
    return streak


@login_required
def index(request):
    projects = Project.objects.filter(user=request.user, archived=False)
    archived_projects = Project.objects.filter(user=request.user, archived=True)
    user_tasks = Task.objects.filter(
        project__user=request.user, project__archived=False, parent__isnull=True
    )
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(is_done=True).count()
    overall_progress = int(completed_tasks / total_tasks * 100) if total_tasks else 0

    today = timezone.localdate()
    today_count = user_tasks.filter(
        Q(due_date=today) | Q(due_date__lt=today, is_done=False)
    ).count()
    streak = _compute_streak(request.user)

    return render(
        request,
        "projects/index.html",
        {
            "projects": projects,
            "archived_projects": archived_projects,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overall_progress": overall_progress,
            "today_count": today_count,
            "streak": streak,
        },
    )


@login_required
def today_view(request):
    today = timezone.localdate()
    tasks = (
        Task.objects.filter(
            project__user=request.user,
            project__archived=False,
            parent__isnull=True,
        )
        .filter(Q(due_date=today) | Q(due_date__lt=today, is_done=False))
        .select_related("project")
        .order_by("is_done", "due_date", "-priority")
    )
    overdue = [t for t in tasks if t.due_date and t.due_date < today and not t.is_done]
    due_today = [t for t in tasks if t.due_date == today]
    return render(
        request,
        "projects/today.html",
        {
            "overdue": overdue,
            "due_today": due_today,
            "total": len(overdue) + len(due_today),
            "today": today,
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
        notify(request.user, "project_created", project=project, name=project.name)
        if request.headers.get("HX-Request"):
            html = render_to_string(
                "projects/_project_card.html", {"project": project}, request=request
            )
            response = HttpResponse(html)
            response["HX-Trigger"] = json.dumps(
                {"showToast": {"message": "Project created!", "type": "success"}}
            )
            return response
        return redirect("index")
    if request.headers.get("HX-Request"):
        return HttpResponse(status=400)
    return redirect("index")


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    tasks = project.tasks.filter(parent__isnull=True).prefetch_related("subtasks")
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
    name = project.name
    project.delete()
    notify(request.user, "project_deleted", name=name)
    messages.success(request, "Project deleted.")
    return redirect("index")


@login_required
@require_POST
def project_archive(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    project.archived = not project.archived
    project.save()
    return redirect("index")


def _all_done_celebrate(project):
    return (
        project.total_tasks > 0
        and project.completed_tasks == project.total_tasks
    )


@login_required
@require_POST
def task_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    raw_title = (request.POST.get("title") or "").strip()
    if not raw_title:
        return HttpResponse(status=400)

    title, parsed_priority, parsed_due = parse_task_input(raw_title)
    if not title:
        title = raw_title

    priority = request.POST.get("priority") or parsed_priority
    due_str = request.POST.get("due_date") or ""
    due_date = parsed_due
    if due_str:
        try:
            due_date = date.fromisoformat(due_str)
        except ValueError:
            pass

    last_order = (
        Task.objects.filter(project=project, parent__isnull=True)
        .aggregate(m=Count("id"))["m"]
        or 0
    )
    task = Task.objects.create(
        project=project,
        title=title,
        priority=priority,
        due_date=due_date,
        order=last_order,
    )
    notify(request.user, "task_created", task=task, title=task.title)

    if request.headers.get("HX-Request"):
        html = render_to_string(
            "projects/_task_row.html",
            {"task": task, "project": project},
            request=request,
        )
        progress_html = render_to_string(
            "projects/_progress.html", {"project": project}, request=request
        )
        response = HttpResponse(html + progress_html)
        triggers = {"showToast": {"message": "Task added!", "type": "success"}}
        response["HX-Trigger"] = json.dumps(triggers)
        return response
    return redirect("project_detail", pk=project.pk)


@login_required
@require_POST
def task_toggle(request, pk):
    task = get_object_or_404(
        Task, pk=pk, project__user=request.user
    )
    was_done = task.is_done
    task.is_done = not task.is_done
    task.completed_at = timezone.now() if task.is_done else None
    task.save()
    if not was_done and task.is_done and task.parent is None:
        notify(
            request.user,
            "task_completed",
            task=task,
            title=task.title,
            project_progress=task.project.progress,
            all_done=_all_done_celebrate(task.project),
        )

    if request.headers.get("HX-Request"):
        html = render_to_string(
            "projects/_task_row.html",
            {"task": task, "project": task.project},
            request=request,
        )
        progress_html = render_to_string(
            "projects/_progress.html", {"project": task.project}, request=request
        )
        response = HttpResponse(html + progress_html)
        triggers = {}
        if task.is_done and _all_done_celebrate(task.project):
            triggers["confetti"] = {"message": f"All tasks done in {task.project.name}!"}
        if triggers:
            response["HX-Trigger"] = json.dumps(triggers)
        return response
    return redirect("project_detail", pk=task.project.pk)


@login_required
@require_http_methods(["DELETE", "POST"])
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, project__user=request.user)
    project = task.project
    title = task.title
    is_subtask = task.parent is not None
    task.delete()
    if not is_subtask:
        notify(request.user, "task_deleted", title=title, project_name=project.name)
    if request.headers.get("HX-Request"):
        progress_html = render_to_string(
            "projects/_progress.html", {"project": project}, request=request
        )
        response = HttpResponse(progress_html)
        response["HX-Trigger"] = json.dumps(
            {"showToast": {"message": "Task deleted", "type": "info"}}
        )
        return response
    return redirect("project_detail", pk=project.pk)


@login_required
@require_POST
def task_reorder(request):
    try:
        payload = json.loads(request.body.decode())
        ids = payload.get("ids", [])
    except (ValueError, AttributeError):
        return HttpResponseBadRequest("bad payload")
    tasks = {
        t.id: t
        for t in Task.objects.filter(id__in=ids, project__user=request.user)
    }
    for order, tid in enumerate(ids):
        t = tasks.get(int(tid))
        if t:
            t.order = order
            t.save(update_fields=["order"])
    return JsonResponse({"ok": True})


@login_required
@require_POST
def subtask_add(request, parent_pk):
    parent = get_object_or_404(Task, pk=parent_pk, project__user=request.user)
    title = (request.POST.get("title") or "").strip()
    if not title:
        return HttpResponse(status=400)
    last_order = parent.subtasks.count()
    sub = Task.objects.create(
        project=parent.project,
        parent=parent,
        title=title,
        order=last_order,
    )
    html = render_to_string(
        "projects/_subtask_row.html", {"sub": sub, "parent": parent}, request=request
    )
    return HttpResponse(html)


@login_required
@require_POST
def subtask_toggle(request, pk):
    sub = get_object_or_404(
        Task, pk=pk, project__user=request.user, parent__isnull=False
    )
    sub.is_done = not sub.is_done
    sub.completed_at = timezone.now() if sub.is_done else None
    sub.save()
    html = render_to_string(
        "projects/_subtask_row.html",
        {"sub": sub, "parent": sub.parent},
        request=request,
    )
    return HttpResponse(html)


@login_required
@require_http_methods(["DELETE", "POST"])
def subtask_delete(request, pk):
    sub = get_object_or_404(
        Task, pk=pk, project__user=request.user, parent__isnull=False
    )
    sub.delete()
    return HttpResponse(status=200)


@login_required
def search(request):
    query = request.GET.get("q", "").strip()
    tasks = []
    if query:
        tasks = (
            Task.objects.filter(
                project__user=request.user, title__icontains=query
            )
            .select_related("project")[:20]
        )
    return render(request, "projects/_search.html", {"tasks": tasks, "query": query})


@login_required
def settings_view(request):
    prefs = EmailPreference.for_user(request.user)
    if request.method == "POST":
        prefs.enabled = "enabled" in request.POST
        prefs.project_created = "project_created" in request.POST
        prefs.project_deleted = "project_deleted" in request.POST
        prefs.task_created = "task_created" in request.POST
        prefs.task_completed = "task_completed" in request.POST
        prefs.task_deleted = "task_deleted" in request.POST
        email = (request.POST.get("email") or "").strip()
        if email and email != request.user.email:
            request.user.email = email
            request.user.save(update_fields=["email"])
        prefs.save()
        if request.headers.get("HX-Request"):
            response = HttpResponse(status=204)
            response["HX-Trigger"] = json.dumps(
                {"showToast": {"message": "Settings saved!", "type": "success"}}
            )
            return response
        messages.success(request, "Settings saved.")
        return redirect("settings")
    return render(request, "projects/settings.html", {"prefs": prefs})


@login_required
def palette(request):
    query = request.GET.get("q", "").strip()
    projects = []
    tasks = []
    if query:
        projects = Project.objects.filter(
            user=request.user, name__icontains=query, archived=False
        )[:5]
        tasks = (
            Task.objects.filter(
                project__user=request.user,
                title__icontains=query,
                parent__isnull=True,
            )
            .select_related("project")[:8]
        )
    else:
        projects = Project.objects.filter(user=request.user, archived=False)[:5]
    return render(
        request,
        "projects/_palette.html",
        {"projects": projects, "tasks": tasks, "query": query},
    )
