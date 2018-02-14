from flask import g, request, jsonify
from flask_restful import Resource

from ...auth.validation import validate_request, validate_input_data
from ...helper.error_message import moov_errors
from ...helper.camel_to_snake import camel_to_snake
from ...models import User, Wallet
from ...schema import user_signup_schema


class UserSignupResource(Resource):
    
    @validate_request()
    def post(self):
        json_input = request.get_json()
        
        keys = ['firstname', 'lastname', 'email', 'image_url']

        _user = {}
        if validate_input_data(json_input, keys, _user):
            return validate_input_data(json_input, keys, _user)

        data, errors = user_signup_schema.load(json_input)
        if errors:
            return moov_errors(errors, 422)

        if User.is_user_data_taken(json_input['email']):
            return moov_errors('User already exists', 400)
            
        new_user = User(
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            image_url=data['image_url'] if json_input.get('image_url') else "https://pixabay.com/en/blank-profile-picture-mystery-man-973461/",
        )
        new_user.save()

        message = "The profile with email {0} has been created succesfully".format(new_user.email)

        _data, _ = user_signup_schema.dump(new_user)

        return {
            'status': 'success',
            'data': {
                'user': _data,
                'message': message
            }
        }, 201
