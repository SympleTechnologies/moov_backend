try:
    from ..models import Notification
    from ..schema import notification_schema
except ImportError:
    from moov_backend.api.models import Notification
    from moov_backend.api.schema import notification_schema


# save notifications
def save_notification(recipient_id, sender_id, message, transaction_icon_id):
    new_notification = Notification(
        message=message,
        recipient_id=recipient_id,
        sender_id=sender_id,
        transaction_icon_id=transaction_icon_id
    )
    new_notification.save()
    return notification_schema.dump(new_notification)
