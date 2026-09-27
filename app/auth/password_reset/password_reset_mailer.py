from typing import Protocol


class PasswordResetMailer(Protocol):
    def send_password_reset(
        self,
        email: str,
        raw_token: str,
    ) -> None: ...
