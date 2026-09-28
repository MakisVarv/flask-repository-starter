import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from app.auth.password_reset.password_reset_exceptions import PasswordResetDeliveryError


class SMTPPasswordResetMailer:
    def __init__(
        self,
        host: str,
        port: int,
        sender: str,
        frontend_origin: str,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = False,
    ) -> None:
        self.host = host
        self.port = port
        self.sender = sender
        self.frontend_origin = frontend_origin.rstrip("/")
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def send_password_reset(
        self,
        email: str,
        raw_token: str,
    ) -> None:
        query = urlencode({"token": raw_token})

        reset_url = f"{self.frontend_origin}/reset-password?{query}"

        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = email
        message["Subject"] = "Reset your password"

        message.set_content(
            "You requested a password reset.\n\n"
            f"Reset your password here:\n{reset_url}\n\n"
            "If you did not request this, you can ignore this email."
        )
        try:
            with smtplib.SMTP(self.host, self.port) as smtp:
                if self.use_tls:
                    context = ssl.create_default_context()
                    smtp.starttls(context=context)

                if self.username and self.password:
                    smtp.login(
                        self.username,
                        self.password,
                    )

                smtp.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            raise PasswordResetDeliveryError(
                "Failed to deliver password reset email."
            ) from exc
