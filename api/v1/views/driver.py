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
    from ...auth.validation import validate_request, validate_input_data, validate_empty_string
    from ...helper.error_message import moov_errors, not_found_errors
    from ...models import User, UserType, Wallet, Transaction, Notification, FreeRide, Icon
    from ...schema import user_schema, user_login_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.auth.validation import validate_request, validate_input_data, validate_empty_string
    from moov_backend.api.helper.error_message import moov_errors, not_found_errors
    from moov_backend.api.models import User, UserType, Wallet, Transaction, Notification, FreeRide, Icon
    from moov_backend.api.schema import user_schema, user_login_schema


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


class DriverResource(Resource):
    
    @token_required
    @validate_request()
    def put(self):
        pass
    
    @token_required
    @validate_request()
    def delete(self):
        pass
