import logging
from typing import Protocol

from neurix_shared.config import settings

logger = logging.getLogger("neurix.mailer")


class Mailer(Protocol):
    async def send_verification_email(self, to_email: str, verification_link: str) -> None: ...


class LogMailer:
    """Default backend — logs the verification link instead of sending real email.
    Deliberate choice for now (no email provider credentials exist yet), not a stub left
    in by accident. `settings.mailer_backend` picks the implementation in `get_mailer()`
    below; swapping in Resend/SMTP later means adding one more branch there, nothing else
    in the codebase needs to change since callers only depend on the `Mailer` protocol."""

    async def send_verification_email(self, to_email: str, verification_link: str) -> None:
        logger.info("verification_email to=%s link=%s", to_email, verification_link)


def get_mailer() -> Mailer:
    if settings.mailer_backend == "log":
        return LogMailer()
    raise NotImplementedError(f"Unknown mailer_backend: {settings.mailer_backend!r}")


mailer = get_mailer()
