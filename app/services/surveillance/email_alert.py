from datetime import datetime

import yagmail

from app.core import config


class EmailAlertManager:

    def __init__(self):
        self.enabled = config.ENABLE_EMAIL

        if self.enabled:
            try:
                self.yag = yagmail.SMTP(
                    config.EMAIL_USER,
                    config.EMAIL_PASS,
                )

                print("[EMAIL] Email alerts initialized")

            except Exception as e:
                print(
                    f"[EMAIL ERROR] Failed to initialize: {e}"
                )

                self.enabled = False

    # ---------------------------------------------------------
    # Recipient helper
    # ---------------------------------------------------------

    def _recipient(self, recipient_email=None):
        """
        Email recipient must come from the authenticated user.

        There is intentionally NO fallback to EMAIL_RECEIVER.
        """

        if not recipient_email:
            print(
                "[EMAIL ERROR] No recipient email associated "
                "with the current user"
            )
            return None

        return recipient_email

    # ---------------------------------------------------------
    # Person alert
    # ---------------------------------------------------------

    def send_alert(
        self,
        person_id,
        snapshot_path,
        confidence,
        recipient_email=None,
    ):

        if not self.enabled:
            return False

        recipient = self._recipient(
            recipient_email
        )

        if not recipient:
            return False

        try:

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            subject = (
                f"{config.EMAIL_SUBJECT} "
                f"(ID: {person_id})"
            )

            contents = f"""
Security Alert

Person ID: {person_id}
Time: {timestamp}
Confidence: {confidence:.2%}

Snapshot attached.
"""

            self.yag.send(
                to=recipient,
                subject=subject,
                contents=contents,
                attachments=snapshot_path,
            )

            print(
                f"[EMAIL] Alert sent for Person ID "
                f"{person_id} to {recipient}"
            )

            return True

        except Exception as e:

            print(
                f"[EMAIL ERROR] Failed to send: {e}"
            )

            return False

    # ---------------------------------------------------------
    # Fire alert
    # ---------------------------------------------------------

    def send_fire_alert(
        self,
        snapshot_path,
        confidence,
        person_count=0,
        severity="high",
        recipient_email=None,
    ):

        if not self.enabled:
            return False

        recipient = self._recipient(
            recipient_email
        )

        if not recipient:
            return False

        try:

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            subject = (
                f"{config.EMAIL_SUBJECT} - FIRE ALERT"
            )

            contents = f"""
FIRE SECURITY ALERT

Severity: {severity.upper()}
Time: {timestamp}

Fire Confidence: {confidence:.2%}
People Detected: {person_count}

Immediate attention may be required.

Snapshot attached.
"""

            self.yag.send(
                to=recipient,
                subject=subject,
                contents=contents,
                attachments=snapshot_path,
            )

            print(
                f"[EMAIL] Fire alert sent to {recipient}"
            )

            return True

        except Exception as e:

            print(
                f"[EMAIL ERROR] Failed to send fire alert: {e}"
            )

            return False

    # ---------------------------------------------------------
    # Violence alert
    # ---------------------------------------------------------

    def send_voilence_alert(
        self,
        snapshot_path,
        confidence,
        person_count=0,
        severity="high",
        recipient_email=None,
    ):

        if not self.enabled:
            return False

        recipient = self._recipient(
            recipient_email
        )

        if not recipient:
            return False

        try:

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            subject = (
                f"{config.EMAIL_SUBJECT} - VIOLENCE ALERT"
            )

            contents = f"""
VIOLENCE SECURITY ALERT

Severity: {severity.upper()}
Time: {timestamp}

Violence Confidence: {confidence:.2%}
People Detected: {person_count}

Immediate attention may be required.

Snapshot attached.
"""

            self.yag.send(
                to=recipient,
                subject=subject,
                contents=contents,
                attachments=snapshot_path,
            )

            print(
                f"[EMAIL] Violence alert sent to {recipient}"
            )

            return True

        except Exception as e:

            print(
                f"[EMAIL ERROR] Failed to send violence alert: {e}"
            )

            return False

    # ---------------------------------------------------------
    # Crowd alert
    # ---------------------------------------------------------

    def send_crowd_alert(
        self,
        snapshot_path,
        person_count,
        severity="medium",
        recipient_email=None,
    ):

        if not self.enabled:
            return False

        recipient = self._recipient(
            recipient_email
        )

        if not recipient:
            return False

        try:

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            subject = (
                f"{config.EMAIL_SUBJECT} - CROWD ALERT"
            )

            contents = f"""
CROWD SECURITY ALERT

Severity: {severity.upper()}
Time: {timestamp}

People Detected: {person_count}

Unusual crowd activity was detected.

Snapshot attached.
"""

            self.yag.send(
                to=recipient,
                subject=subject,
                contents=contents,
                attachments=snapshot_path,
            )

            print(
                f"[EMAIL] Crowd alert sent to {recipient}"
            )

            return True

        except Exception as e:

            print(
                f"[EMAIL ERROR] Failed to send crowd alert: {e}"
            )

            return False

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    def send_summary(
        self,
        total_detections,
        unique_persons,
        recipient_email=None,
    ):

        if not self.enabled:
            return False

        recipient = self._recipient(
            recipient_email
        )

        if not recipient:
            return False

        try:

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            subject = (
                f"{config.EMAIL_SUBJECT} - SUMMARY"
            )

            contents = f"""
SURVEILLANCE SUMMARY

Time: {timestamp}

Total Detections: {total_detections}
Unique Persons: {unique_persons}
"""

            self.yag.send(
                to=recipient,
                subject=subject,
                contents=contents,
            )

            print(
                f"[EMAIL] Summary sent to {recipient}"
            )

            return True

        except Exception as e:

            print(
                f"[EMAIL ERROR] Failed to send summary: {e}"
            )

            return False