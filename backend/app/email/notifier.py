"""Email notifier stubs.

Provides `compose_digest` and `send` signatures to be implemented later.
"""


class Notifier:
    def __init__(self, smtp_host: str = None):
        self.smtp_host = smtp_host

    def compose_digest(self, items) -> str:
        """Return HTML digest body for items (stub)."""
        raise NotImplementedError("compose_digest is a scaffold stub")

    def send(self, to_address: str, html: str):
        """Send an email (stub)."""
        raise NotImplementedError("send is a scaffold stub")
