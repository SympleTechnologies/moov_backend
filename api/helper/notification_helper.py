try:
    from ..models import Notification
except ImportError:
    from moov_backend.api.models import Notification


# save notifications
def save_notification(recipient_id, sender_id, message):
    new_notification = Notification(
        message= message,
        recipient_id= recipient_id,
        sender_id= sender_id
    )
    new_notification.save()
