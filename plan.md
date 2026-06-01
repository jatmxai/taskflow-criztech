# TaskFlow — Technical Plan
> Django 5 · HTMX · Alpine.js · PostgreSQL · Render

---

## 1. Overview

TaskFlow is a lightweight project management tool that demonstrates modern Django with HTMX for server-driven interactivity and Alpine.js for reactive UI — no heavy JS framework needed.

---

## 2. Technology Stack

| Technology | Version | Purpose |
|---|---|---|
| Django | 5.0 | Backend, ORM, auth, routing |
| HTMX | 2.x | Partial page updates, no full JS framework |
| Alpine.js | 3.x | Dropdowns, modals, toasts (reactive UI) |
| PostgreSQL | 16 | Production database (SQLite local) |
| Gunicorn | 22.x | WSGI production server |
| WhiteNoise | 6.x | Static file serving |
| Render | — | Cloud deployment |

---

## 3. Core Features

### HTMX-powered
- Add tasks inline — no page reload (`hx-post` + `hx-swap`)
- Toggle task complete/incomplete instantly
- Delete task with fade-out (`hx-delete` + `hx-swap="outerHTML swap:500ms"`)
- Live search on keyup (`hx-trigger="keyup changed delay:300ms"`)

### Alpine.js-powered
- Dropdown menus (`x-show` / `x-transition`)
- Toast notifications (success, error, info)
- Confirmation modal before delete
- Animated progress bar (`x-bind:style`)

### Django core
- User auth (login / register / logout)
- Each user sees only their own data
- Django admin for quick data management

---

## 4. Data Models

```python
class Project(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    name       = models.CharField(max_length=120)
    color      = models.CharField(max_length=7, default="#3B82F6")
    archived   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Task(models.Model):
    project    = models.ForeignKey(Project, on_delete=models.CASCADE)
    title      = models.CharField(max_length=255)
    is_done    = models.BooleanField(default=False)
    priority   = models.CharField(max_length=10, default="medium")
    due_date   = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 5. URL Structure

| URL | HTMX? | Description |
|---|---|---|
| `/` | No | Dashboard — all projects |
| `/projects/new/` | Yes | Create project (partial swap) |
| `/projects/<id>/` | No | Task list for a project |
| `/tasks/add/` | Yes | Add task inline |
| `/tasks/<id>/toggle/` | Yes | Complete / uncomplete |
| `/tasks/<id>/delete/` | Yes | Delete with fade-out |
| `/search/` | Yes | Live search results partial |

---

## 6. File Structure

```
taskflow/
├── taskflow/               # settings.py, urls.py, wsgi.py
├── projects/               # main app
│   ├── models.py
│   ├── views.py            # full + partial (HTMX) views
│   ├── urls.py
│   └── templates/projects/
│       ├── _task_row.html  # partial — swapped by HTMX
│       ├── _search.html    # partial — live search
│       ├── index.html
│       └── detail.html
├── templates/
│   └── base.html           # loads HTMX + Alpine via CDN
├── static/
├── requirements.txt
├── render.yaml             # Render deploy config
└── build.sh                # collectstatic + migrate
```

---

## 7. Deployment on Render

### Services
- **Web Service** — Python, starts with `gunicorn taskflow.wsgi`
- **PostgreSQL** — Render free tier (sufficient for demo)

### Environment Variables
| Variable | Value |
|---|---|
| `SECRET_KEY` | Generated Django secret key |
| `DEBUG` | `False` |
| `DATABASE_URL` | Auto-injected by Render |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `PYTHON_VERSION` | `3.12.0` |

### render.yaml
```yaml
services:
  - type: web
    name: taskflow
    runtime: python
    buildCommand: "./build.sh"
    startCommand: "gunicorn taskflow.wsgi"
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: DATABASE_URL
        fromDatabase:
          name: taskflow-db
          property: connectionString

databases:
  - name: taskflow-db
    plan: free
```

---

## 8. Build Timeline

| Phase | Work | Est. Time |
|---|---|---|
| 1 — Setup | Django project, models, admin | ~1 hr |
| 2 — Core Views | CRUD, base templates, Tailwind | ~2 hrs |
| 3 — HTMX | Inline add/toggle/delete, search | ~2 hrs |
| 4 — Alpine.js | Dropdowns, toasts, modals | ~1.5 hrs |
| 5 — Deploy | render.yaml, env vars, go live | ~1 hr |
| **Total** | | **~7.5 hrs** |

---

## 9. Why This Stack?

- **HTMX** — server handles state, views return HTML fragments, no JSON API needed
- **Alpine.js** — handles only ephemeral UI state, no build step, no npm
- **Django** — batteries-included: ORM, auth, admin, migrations all built-in
- **Render** — auto-deploy from GitHub, free PostgreSQL, zero DevOps overhead
