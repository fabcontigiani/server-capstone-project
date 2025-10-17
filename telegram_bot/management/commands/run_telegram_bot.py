from django.core.management.base import BaseCommand

from telegram_bot import bot

class Command(BaseCommand):
    help = "Run telegram bot using long polling (reads TELEGRAM_BOT_TOKEN env var)."

    def add_arguments(self, parser):
        parser.add_argument("--token", help="Optional token; otherwise TELEGRAM_BOT_TOKEN is used.")

    def handle(self, *args, **options):
        token = options.get("token")
        self.stdout.write("Starting telegram bot (polling). Press Ctrl-C to stop.")
        try:
            bot.run(token=token)
        except Exception as exc:
            self.stderr.write(f"Bot exited with error: {exc}")
            raise
