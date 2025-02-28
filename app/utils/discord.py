from discord_webhook import DiscordWebhook
from app.config import settings


def sent_notify_discord(data="busy", is_error=False):
    if is_error:
        webhook = DiscordWebhook(url=settings.discord_errors_url, content=f"{data}")
    else:
        webhook = DiscordWebhook(url=settings.discord_url, content=f"{data}")
    response = webhook.execute()
    return response

def sent_poly_predictions_discord(data):
    webhook = DiscordWebhook(url=settings.poly_content_discord_webhook_url, content=f"{data[:2000]}")
    response = webhook.execute()
    return response

def sent_poly_win_loss_discord(data):
    webhook = DiscordWebhook(url=settings.poly_win_loss_discord_webhook_url, content=f"{data}")
    response = webhook.execute()
    return response