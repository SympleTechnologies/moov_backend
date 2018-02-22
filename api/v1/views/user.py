import os
import datetime
from os.path import join, dirname
from dotenv import load_dotenv

from sqlalchemy import or_
from flask import g, request, jsonify
from flask_restful import Resource
from flask_jwt import jwt

try:
    from ...auth.token import token_required
    from ...auth.validation import validate_request, validate_input_data
    from ...helper.error_message import moov_errors
    from ...models import User, UserType, Wallet, Transaction
    from ...schema import user_schema, user_login_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.auth.validation import validate_request, validate_input_data
    from moov_backend.api.helper.error_message import moov_errors
    from moov_backend.api.models import User, UserType, Wallet, Transaction
    from moov_backend.api.schema import user_schema, user_login_schema


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


class UserResource(Resource):
    
    @token_required
    @validate_request()
    def delete(self):
        json_input = request.get_json()
        if "email" not in json_input:
            return moov_errors("Please provide email of user to delete", 400)

        keys = ['email']
        if validate_input_data(json_input, keys):
            return validate_input_data(json_input, keys)

        _current_user_id = g.current_user.id
        _current_user = User.query.get(_current_user_id)
        _user_to_delete = User.query.filter(User.email==json_input["email"]).first()
        if not _current_user or not _user_to_delete:
            return moov_errors("User does not exist", 404)

        if _user_to_delete.user_type.title == "admin" or \
           _user_to_delete.user_type.title == "school" or \
           _user_to_delete.user_type.title == "car_owner" or \
           _user_to_delete.user_type.title == "moov":
            return moov_errors("Unauthorized, you cannot create a/an {0}".format(_user_to_delete.user_type.title), 401)

        if str(_current_user.email) != str(_user_to_delete.email) and \
        str(_current_user.user_type.title) != "admin":
            return moov_errors("Unauthorized access. You cannot delete this user", 401)

        user_wallet = Wallet.query.filter(Wallet.user_id==_user_to_delete.id).first()
        user_transaction = Transaction.query.filter(or_(Transaction.receiver_wallet_id.like(user_wallet.id),
                                        Transaction.sender_wallet_id.like(user_wallet.id))).first()
        if user_transaction:
            return moov_errors("Please contact admin to deactivate account", 401)

        user_wallet.delete()
        _user_to_delete.delete()

        return {
            'status': 'success',
            'data': None
        }, 200


class UserSignupResource(Resource):
    
    @validate_request()
    def post(self):
        json_input = request.get_json()
        
        keys = ['user_type', 'firstname', 'lastname', 'email', 'image_url']

        _user = {}
        if validate_input_data(json_input, keys, _user):
            return validate_input_data(json_input, keys, _user)

        data, errors = user_schema.load(json_input)
        if errors:
            return moov_errors(errors, 422)

        if User.is_user_data_taken(json_input['email']):
            return moov_errors('User already exists', 400)

        user_type = UserType.query.filter(UserType.title==data['user_type'].lower()).first()
        user_type_id = user_type.id if user_type else None
        if data['user_type'].lower() == "admin" or \
           data['user_type'].lower() == "school" or \
           data['user_type'].lower() == "car_owner" or \
           data['user_type'].lower() == "moov":
            return moov_errors("Unauthorized, you cannot create a/an {0}".format(data['user_type']), 401)
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
            description = "{0} {1}'s Wallet".format((new_user.lastname).title(), (new_user.firstname).title())
        )
        user_wallet.save()

        exp_date = datetime.datetime.utcnow()
        payload = {
                    "id": new_user.id,
                    "exp": exp_date + datetime.timedelta(days=3)
                }
        _token = jwt.encode(payload, os.getenv("TOKEN_KEY"), algorithm='HS256')

        message = "The profile with email {0} has been created succesfully".format(new_user.email)

        _data, _ = user_schema.dump(new_user)
        _data["wallet_amount"] = user_wallet.wallet_amount
        _data["user_type"] = new_user.user_type.title
        return {
            'status': 'success',
            'data': {
                'user': _data,
                'message': message,
                'token': _token
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

        _user_wallet = Wallet.query.filter(Wallet.user_id==_user.id).first()

        exp_date = datetime.datetime.utcnow()
        payload = {
                    "id": _user.id,
                    "exp": exp_date + datetime.timedelta(days=3)
                }
        _token = jwt.encode(payload, os.getenv("TOKEN_KEY"), algorithm='HS256')

        _data, _ = user_schema.dump(_user)
        _data["wallet_amount"] = _user_wallet.wallet_amount if _user_wallet else "Unavailable"
        _data["user_type"] = _user.user_type.title
        return jsonify({"status": "success",
                        "data": {
                            "data": _data,
                            "message": "Login successful",
                            "token": str(_token)
                        }
                    })
