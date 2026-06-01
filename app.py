"""Shim so `gunicorn app:app` (Render's default) resolves to the Django WSGI app."""
from taskflow.wsgi import application as app

__all__ = ["app"]
