import os
import smtplib
import socket
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any, Dict, Optional


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_production_environment() -> bool:
    if _env_flag("FORCE_ERROR_ALERT_EMAILS", False):
        return True

    env_markers = (
        os.getenv("PYTHON_ENV"),
        os.getenv("FLASK_ENV"),
        os.getenv("APP_ENV"),
        os.getenv("RAILWAY_ENVIRONMENT"),
    )
    if any(value and value.strip().lower() == "production" for value in env_markers):
        return True

    return os.getenv("DYNO") is not None


def _build_email_body(
    operation: str,
    recipe_url: str,
    error_message: str,
    recipe_id: Optional[Any],
    extra_context: Optional[Dict[str, Any]],
) -> str:
    safe_recipe_url = recipe_url.strip() if isinstance(recipe_url, str) and recipe_url.strip() else "(missing recipe URL)"
    lines = [
        "A production error occurred in Recipe Audio.",
        "",
        f"Time (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"Operation: {operation}",
        f"Recipe URL: {safe_recipe_url}",
        f"Recipe ID: {recipe_id if recipe_id is not None else '(not provided)'}",
        f"Server: {socket.gethostname()}",
        "",
        "Error details:",
        error_message or "(no error message provided)",
    ]

    if extra_context:
        lines.append("")
        lines.append("Additional context:")
        for key in sorted(extra_context.keys()):
            lines.append(f"- {key}: {extra_context[key]}")

    return "\n".join(lines)


def send_production_error_email(
    *,
    operation: str,
    recipe_url: str,
    error_message: str,
    recipe_id: Optional[Any] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> None:
    if not is_production_environment():
        return

    recipient = os.getenv("ERROR_ALERT_RECIPIENT_EMAIL")
    sender = os.getenv("ERROR_ALERT_SENDER_EMAIL") or os.getenv("SMTP_USERNAME")
    smtp_host = os.getenv("SMTP_HOST")
    use_ssl = _env_flag("SMTP_USE_SSL", False)
    smtp_port_raw = os.getenv("SMTP_PORT", "465" if use_ssl else "587")
    try:
        smtp_port = int(smtp_port_raw)
    except (TypeError, ValueError):
        smtp_port = 465 if use_ssl else 587
        print(f"Invalid SMTP_PORT value '{smtp_port_raw}'. Falling back to {smtp_port}.")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    use_tls = _env_flag("SMTP_USE_TLS", True)

    if not recipient:
        print("Skipping production error email: ERROR_ALERT_RECIPIENT_EMAIL is not configured.")
        return
    if not sender:
        print("Skipping production error email: ERROR_ALERT_SENDER_EMAIL (or SMTP_USERNAME) is not configured.")
        return
    if not smtp_host:
        print("Skipping production error email: SMTP_HOST is not configured.")
        return

    message = EmailMessage()
    message["Subject"] = f"[Recipe Audio] Production error in {operation}"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        _build_email_body(
            operation=operation,
            recipe_url=recipe_url,
            error_message=error_message,
            recipe_id=recipe_id,
            extra_context=extra_context,
        )
    )

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(
                smtp_host,
                smtp_port,
                timeout=10,
                context=ssl.create_default_context(),
            ) as smtp:
                if smtp_username and smtp_password:
                    smtp.login(smtp_username, smtp_password)
                smtp.send_message(message)
            return

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
            smtp.ehlo()
            if use_tls:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            if smtp_username and smtp_password:
                smtp.login(smtp_username, smtp_password)
            smtp.send_message(message)
    except Exception as exc:
        print(f"Failed to send production error email for {operation}: {exc}")
