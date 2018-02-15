import os

from ..models import User, UserType

def create_default_user_types():
    user_types = ['admin', 'driver', 'student']
    for user_type in user_types:
        user_type = UserType(
            title=user_type,
            description='{} privilege'.format(user_type)
        )
        user_type.save()

def create_default_user(user_type_id):
    super_user = User(
            user_type_id=user_type_id,
            firstname="admin",
            lastname="admin",
            image_url="https://pixabay.com/en/blank-profile-picture-mystery-man-973461/",
            email=os.environ.get('ADMIN_EMAIL')
        )
    super_user.save()
