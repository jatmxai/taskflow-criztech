# TaskFlow

> A lightweight project management app — **Django 5 + HTMX + Alpine.js + Tailwind**.

Demonstrates server-driven interactivity (HTMX), reactive UI without a build step (Alpine.js), and Django's batteries-included backend. No JSON API, no npm, no frontend framework.

## Features

- 🗂️ **Projects** with custom colors, archive/unarchive, delete with confirmation
- ✅ **Tasks** with priority (low / medium / high) and optional due dates
- ⚡ **HTMX-powered** — inline task add/toggle/delete, live search, animated progress
- 🎨 **Alpine.js** — dropdowns, modals, toast notifications, smooth transitions
- 🔐 **Auth** — register / login / logout, each user sees only their own data
- 🛠️ **Django admin** at `/admin/` for quick data management

## Quick start (local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. (Optional) Create a superuser for /admin/
python manage.py createsuperuser

# 4. Run the dev server
python manage.py runserver
```

Then open <http://127.0.0.1:8000>. Register a new account and create your first project.

## Project structure

```
taskflow-criztech/
├── taskflow/               # Django project config (settings, urls, wsgi)
├── projects/               # Main app
│   ├── models.py           # Project + Task models
│   ├── views.py            # Full + HTMX partial views
│   ├── forms.py
│   ├── urls.py
│   └── templates/projects/
│       ├── index.html      # Dashboard (projects grid)
│       ├── detail.html     # Tasks for a project
│       ├── _project_card.html
│       ├── _task_row.html  # HTMX-swapped partial
│       ├── _progress.html  # Out-of-band progress update
│       └── _search.html    # Live search results
├── templates/
│   ├── base.html           # Loads HTMX + Alpine + Tailwind via CDN
│   └── registration/       # login.html, register.html
├── requirements.txt
├── render.yaml             # Render deploy config
└── build.sh                # collectstatic + migrate (Render build)
```

## URL map

| URL | HTMX | Purpose |
|---|---|---|
| `/` | | Dashboard — all projects |
| `/projects/new/` | ✓ | Create project (returns card fragment) |
| `/projects/<id>/` | | Task list for a project |
| `/projects/<id>/archive/` | | Toggle archive |
| `/projects/<id>/delete/` | | Delete (with Alpine confirm modal) |
| `/tasks/add/<project_id>/` | ✓ | Add task inline + OOB progress swap |
| `/tasks/<id>/toggle/` | ✓ | Complete / uncomplete |
| `/tasks/<id>/delete/` | ✓ | Delete with fade-out |
| `/search/` | ✓ | Live search across all your tasks |

## Deploy to Render

1. Push this repo to GitHub.
2. In Render, create a **new Blueprint** and point it at the repo — `render.yaml` provisions both the web service and a free PostgreSQL database.
3. First deploy runs `build.sh` (installs deps, collects static, migrates). After it's live, create your superuser via the Render shell:
   ```bash
   python manage.py createsuperuser
   ```

Environment variables (auto-set by `render.yaml`):

| Variable | Value |
|---|---|
| `SECRET_KEY` | auto-generated |
| `DEBUG` | `False` |
| `DATABASE_URL` | injected from the `taskflow-db` database |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `PYTHON_VERSION` | `3.12.0` |

## Tech stack

| | |
|---|---|
| Django 5.0 | backend, ORM, auth, admin, routing |
| HTMX 2.x | server-driven partial updates |
| Alpine.js 3.x | reactive UI (dropdowns, modals, toasts) |
| Tailwind (CDN) | styling |
| PostgreSQL 16 | production database (SQLite locally) |
| Gunicorn | WSGI server |
| WhiteNoise | static file serving |

## Why this stack?

- **HTMX** — server returns HTML fragments, no JSON API, no client-side state to keep in sync.
- **Alpine.js** — handles only ephemeral UI state (open/closed, hover). No build step, no npm.
- **Django** — auth, ORM, admin, migrations all included.
- **Render** — auto-deploy from GitHub, free PostgreSQL, zero DevOps.
