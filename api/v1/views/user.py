import os
import datetime
from os.path import join, dirname
from dotenv import load_dotenv

from flask import g, request, jsonify
from flask_restful import Resource
from flask_jwt import jwt

from ...auth.validation import validate_request, validate_input_data
from ...helper.error_message import moov_errors
from ...helper.camel_to_snake import camel_to_snake
from ...models import User, UserType, Wallet
from ...schema import user_signup_schema, user_login_schema


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


class UserSignupResource(Resource):
    
    @validate_request()
    def post(self):
        json_input = request.get_json()
        
        keys = ['user_type', 'firstname', 'lastname', 'email', 'image_url']

        _user = {}
        if validate_input_data(json_input, keys, _user):
            return validate_input_data(json_input, keys, _user)

        data, errors = user_signup_schema.load(json_input)
        if errors:
            return moov_errors(errors, 422)

        if User.is_user_data_taken(json_input['email']):
            return moov_errors('User already exists', 400)

        user_type = UserType.query.filter(UserType.title==data['user_type'].lower()).first()
        user_type_id = user_type.id if user_type else None
        if data['user_type'].lower() == "admin":
            return moov_errors("Unauthorized, you cannot create an admin", 401)
        if not user_type_id:
            return moov_errors("User type can only be student or driver", 400)
            
        new_user = User(
            user_type_id=user_type_id,
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            image_url=data['image_url'] if json_input.get('image_url') else "https://pixabay.com/en/blank-profile-picture-mystery-man-973461/",
        )
        new_user.save()

        user_wallet = Wallet(
            wallet_amount= 0.00,
            user_id = new_user.id,
        )
        user_wallet.save()

        message = "The profile with email {0} has been created succesfully".format(new_user.email)

        _data, _ = user_signup_schema.dump(new_user)

        return {
            'status': 'success',
            'data': {
                'user': _data,
                'message': message
            }
        }, 201

    
class UserLoginResource(Resource):
        
    @validate_request()
    def post(self):
        json_input = request.get_json()

        keys = ['email']
        if validate_input_data(json_input, keys):
            return validate_input_data(json_input, keys)

        data, errors = user_login_schema.load(json_input)
        if errors:
            return moov_errors(errors, 422)

        _user = User.query.filter(User.email.like(json_input['email'])).first()
        if not _user:
            return moov_errors('User does not exist', 404)

        exp_date = datetime.datetime.utcnow()
        payload = {
                    "id": _user.id,
                    "exp": exp_date + datetime.timedelta(days=3),
                    "user_type": _user.user_type.title
                }
        _token = jwt.encode(payload, os.getenv("TOKEN_KEY"), algorithm='HS256')

        return jsonify({"status": "success",
                        "data": {
                            "message": "Login successful",
                            "token": str(_token)
                        }
                    })
