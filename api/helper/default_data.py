import os

from ..models import User, UserType, PercentagePrice, Wallet

def create_default_user_types():
    user_types = ['admin', 'driver', 'student', 'moov', 'school', 'car_owner']
    for user_type in user_types:
        user_type = UserType(
            title=user_type,
            description='{} privilege'.format(user_type)
        )
        user_type.save()

def create_user(user_type_id, name, email):
    new_user = User(
                    user_type_id=user_type_id,
                    firstname=name,
                    lastname=name,
                    image_url="https://pixabay.com/en/blank-profile-picture-mystery-man-973461/",
                    email=email
                )
    new_user.save()
    return new_user

def create_percentage_price(title, price, description):
    new_percentage_price = PercentagePrice(
                                title= title,
                                price= price,
                                description= "{0}'s percentage price".format(description)        
                            )
    return new_percentage_price.save()

def create_wallet(user_id, wallet_amount, description):
    new_wallet = Wallet(
                    user_id= user_id,
                    wallet_amount= wallet_amount,
                    description= description
                )
    return new_wallet.save()
