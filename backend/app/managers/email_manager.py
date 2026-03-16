from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Email, Mail, To

from backend.app.core.config import Settings
from backend.app.schemas import EmailPayload


logger = logging.getLogger(__name__)
TOKEN_PATTERN = re.compile(r"{{\s*(?P<key>[a-zA-Z0-9_]+)\s*}}")


@dataclass
class RenderedEmail:
    subject: str
    html: str


class EmailManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._templates_dir = Path(settings.email_templates_dir)

    def _load_template(self, template_name: str) -> str:
        template_path = self._templates_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Email template not found: {template_path}")
        return template_path.read_text(encoding="utf-8")

    def _replace_tokens(self, raw: str, context: dict[str, Any]) -> str:
        def replace(match: re.Match[str]) -> str:
            key = match.group("key")
            return str(context.get(key, ""))

        return TOKEN_PATTERN.sub(replace, raw)

    def render_template(self, template_name: str, context: dict[str, Any]) -> RenderedEmail:
        css = self._load_template("email.css")
        base = self._load_template("base.html")
        body = self._replace_tokens(self._load_template(template_name), context)
        html = self._replace_tokens(base, {**context, "body": body, "css": css})
        return RenderedEmail(subject=str(context.get("subject", self._settings.app_name)), html=html)

    def send_email(self, payload: EmailPayload) -> dict[str, Any]:
        rendered = self.render_template(payload.template_name, {**payload.context, "subject": payload.subject})
        if not self._settings.sendgrid_api_key:
            logger.info("EMAIL_DRY_RUN to=%s subject=%s", payload.to_email, rendered.subject)
            return {"status": "dry-run", "to": str(payload.to_email), "subject": rendered.subject}

        message = Mail(
            from_email=Email(self._settings.email_from, self._settings.email_from_name),
            to_emails=To(str(payload.to_email)),
            subject=rendered.subject,
            plain_text_content="Please view this email in an HTML-capable client.",
            html_content=rendered.html,
        )
        response = SendGridAPIClient(self._settings.sendgrid_api_key).send(message)
        return {"status": "sent", "status_code": response.status_code}

    def send_auth_email(self, *, to_email: str, verification_link: str, user_name: str) -> dict[str, Any]:
        return self.send_email(
            EmailPayload(
                to_email=to_email,
                subject="Verify your Labib account",
                template_name="auth_code.html",
                context={"user_name": user_name, "action_url": verification_link},
            )
        )

    def send_password_reset(self, *, to_email: str, reset_link: str, user_name: str) -> dict[str, Any]:
        return self.send_email(
            EmailPayload(
                to_email=to_email,
                subject="Reset your Labib password",
                template_name="password_reset.html",
                context={"user_name": user_name, "action_url": reset_link},
            )
        )

    def send_registration_approval(self, *, to_email: str, dashboard_link: str, user_name: str) -> dict[str, Any]:
        return self.send_email(
            EmailPayload(
                to_email=to_email,
                subject="Your Labib registration was approved",
                template_name="registration_approval.html",
                context={"user_name": user_name, "action_url": dashboard_link},
            )
        )

    def send_new_proposal_alert(self, *, to_email: str, dashboard_link: str, user_name: str) -> dict[str, Any]:
        return self.send_email(
            EmailPayload(
                to_email=to_email,
                subject="A new refinance proposal is available",
                template_name="new_proposal_alert.html",
                context={"user_name": user_name, "action_url": dashboard_link},
            )
        )
