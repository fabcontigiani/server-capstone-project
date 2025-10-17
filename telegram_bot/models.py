from django.db import models


class TelegramUser(models.Model):
    """Store Telegram chat IDs for users who have started the bot."""
    chat_id = models.BigIntegerField(unique=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.first_name or self.username or self.chat_id} ({self.chat_id})"
