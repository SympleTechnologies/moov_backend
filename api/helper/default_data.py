import os

from ..models import User, UserType

def create_default_user_types():
    user_types = ['admin', 'driver', 'student', 'moov', 'school', 'car_owner']
    for user_type in user_types:
        user_type = UserType(
            title=user_type,
            description='{} privilege'.format(user_type)
        )
        user_type.save()

def create_user(user_type_id, name, email):
    return User(
                user_type_id=user_type_id,
                firstname=name,
                lastname=name,
                image_url="https://pixabay.com/en/blank-profile-picture-mystery-man-973461/",
                email=email
            )
