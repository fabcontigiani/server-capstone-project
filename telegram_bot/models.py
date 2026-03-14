from django.db import models


class TelegramUser(models.Model):
    """Store Telegram chat IDs for users who have started the bot."""
    chat_id = models.BigIntegerField(unique=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.first_name or self.username or self.chat_id} ({self.chat_id})"


class BotSettings(models.Model):
    """Global bot configuration (singleton – only one row)."""
    threshold = models.IntegerField(
        default=0,
        help_text="Minimum top-classification score (0-100) to send notifications.",
    )

    class Meta:
        verbose_name = "Bot Settings"
        verbose_name_plural = "Bot Settings"

    def __str__(self) -> str:
        return f"BotSettings(threshold={self.threshold})"

    @classmethod
    def get_threshold(cls) -> int:
        """Return the current global threshold, creating the row if needed."""
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"threshold": 0})
        return obj.threshold

    @classmethod
    def set_threshold(cls, value: int) -> None:
        """Update (or create) the global threshold."""
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"threshold": value})
        if obj.threshold != value:
            obj.threshold = value
            obj.save(update_fields=["threshold"])
