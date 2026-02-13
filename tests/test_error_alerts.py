import os
import unittest
from unittest.mock import patch

from error_alerts import send_production_error_email


class ProductionErrorAlertTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    @patch("error_alerts.smtplib.SMTP")
    def test_does_not_send_when_not_in_production(self, smtp_mock):
        os.environ.update(
            {
                "ERROR_ALERT_RECIPIENT_EMAIL": "alerts@example.com",
                "ERROR_ALERT_SENDER_EMAIL": "no-reply@example.com",
                "SMTP_HOST": "smtp.example.com",
            }
        )
        send_production_error_email(
            operation="extract_recipe",
            recipe_url="https://example.com/recipe",
            error_message="scraper failed",
        )
        smtp_mock.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch("error_alerts.smtplib.SMTP")
    def test_sends_email_in_production_with_tls(self, smtp_class_mock):
        os.environ.update(
            {
                "PYTHON_ENV": "production",
                "ERROR_ALERT_RECIPIENT_EMAIL": "alerts@example.com",
                "ERROR_ALERT_SENDER_EMAIL": "no-reply@example.com",
                "SMTP_HOST": "smtp.example.com",
                "SMTP_PORT": "587",
                "SMTP_USERNAME": "smtp-user",
                "SMTP_PASSWORD": "smtp-pass",
                "SMTP_USE_TLS": "true",
            }
        )

        smtp_instance = smtp_class_mock.return_value.__enter__.return_value

        send_production_error_email(
            operation="generate_audio",
            recipe_url="https://example.com/recipe",
            error_message="tts failed",
            recipe_id=42,
        )

        smtp_class_mock.assert_called_once_with("smtp.example.com", 587, timeout=10)
        smtp_instance.starttls.assert_called_once()
        smtp_instance.login.assert_called_once_with("smtp-user", "smtp-pass")
        smtp_instance.send_message.assert_called_once()

        sent_message = smtp_instance.send_message.call_args[0][0]
        self.assertEqual(sent_message["To"], "alerts@example.com")
        self.assertIn("https://example.com/recipe", sent_message.get_content())
        self.assertIn("generate_audio", sent_message["Subject"])

    @patch.dict(os.environ, {}, clear=True)
    @patch("error_alerts.smtplib.SMTP")
    def test_skips_when_required_email_config_missing(self, smtp_mock):
        os.environ.update(
            {
                "PYTHON_ENV": "production",
                "ERROR_ALERT_SENDER_EMAIL": "no-reply@example.com",
                "SMTP_HOST": "smtp.example.com",
            }
        )

        send_production_error_email(
            operation="extract_recipe",
            recipe_url="https://example.com/recipe",
            error_message="parse failed",
        )

        smtp_mock.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch("error_alerts.smtplib.SMTP")
    def test_invalid_smtp_port_falls_back_to_default(self, smtp_class_mock):
        os.environ.update(
            {
                "PYTHON_ENV": "production",
                "ERROR_ALERT_RECIPIENT_EMAIL": "alerts@example.com",
                "ERROR_ALERT_SENDER_EMAIL": "no-reply@example.com",
                "SMTP_HOST": "smtp.example.com",
                "SMTP_PORT": "not-a-number",
            }
        )

        send_production_error_email(
            operation="extract_recipe",
            recipe_url="https://example.com/recipe",
            error_message="scrape failed",
        )

        smtp_class_mock.assert_called_once_with("smtp.example.com", 587, timeout=10)


if __name__ == "__main__":
    unittest.main()
