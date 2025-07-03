from flask_login import current_user
from app.models import Notification

def inject_notifications():
    if current_user.is_authenticated:
        notifications = Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).order_by(Notification.timestamp.desc()).all()
    else:
        notifications = []
    return dict(notifications=notifications)