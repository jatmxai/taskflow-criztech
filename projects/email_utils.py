"""Background email sender with branded HTML + plain text templates.

Sends fire-and-forget in a background thread so requests don't block on SMTP.
Errors are swallowed by `fail_silently=True` — email is best-effort.
"""

import logging
import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import EmailPreference

logger = logging.getLogger(__name__)


EVENT_TEMPLATES = {
    "project_created": ("emails/project_created.html", "Project created: {name}"),
    "project_deleted": ("emails/project_deleted.html", "Project deleted: {name}"),
    "task_created":    ("emails/task_created.html",    "New task: {title}"),
    "task_completed":  ("emails/task_completed.html",  "Completed: {title}"),
    "task_deleted":    ("emails/task_deleted.html",    "Task deleted: {title}"),
}


def _send(subject: str, html: str, text: str, to_email: str):
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=True)
    except Exception as exc:
        logger.warning("Email send failed: %s", exc)


def notify(user, event: str, **context):
    """Send a notification email if the user has opted in for this event.

    Looks up template + subject from EVENT_TEMPLATES. Renders both HTML and a
    plain-text fallback. Dispatches via a background thread.
    """
    if not user.email:
        return
    if event not in EVENT_TEMPLATES:
        return

    prefs = EmailPreference.for_user(user)
    if not prefs.enabled or not getattr(prefs, event, False):
        return

    template_name, subject_template = EVENT_TEMPLATES[event]
    subject = subject_template.format(**context)

    ctx = {
        "subject": subject,
        "site_url": settings.SITE_URL,
        "user": user,
        **context,
    }
    html = render_to_string(template_name, ctx)
    text = strip_tags(html)

    threading.Thread(
        target=_send,
        args=(subject, html, text, user.email),
        daemon=True,
    ).start()
