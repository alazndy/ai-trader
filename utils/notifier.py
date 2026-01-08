import requests
from utils.logger import setup_logger
import os

logger = setup_logger("Notifier")

def send_notification(title, message, priority='default'):
    """
    Sends a push notification via ntfy.sh.
    
    Args:
        title (str): Notification title.
        message (str): Body text.
        priority (str): 'default', 'high', 'urgent'.
    """
    # Load topic from env or use a default/fallback
    topic = os.getenv("NTFY_TOPIC", "aitrader_test")
    
    url = f"https://ntfy.sh/{topic}"
    
    try:
        response = requests.post(
            url,
            data=message.encode('utf-8'),
            headers={
                "Title": title.encode('utf-8'),
                "Priority": priority
            }
        )
        if response.status_code == 200:
            logger.info("Notification sent successfully.")
        else:
            logger.warning(f"Failed to send notification. Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
