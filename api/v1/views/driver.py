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
    from ...auth.validation import (
        validate_request, validate_input_data, validate_empty_string
    )
    from ...helper.common_helper import (
        is_empty_request_fields, remove_unwanted_keys
    )
    from ...helper.error_message import moov_errors, not_found_errors
    from ...models import DriverInfo, AdmissionType
    from ...schema import user_schema, driver_info_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.auth.validation import (
        validate_request, validate_input_data, validate_empty_string
    )
    from moov_backend.api.helper.common_helper import (
        is_empty_request_fields, remove_unwanted_keys
    )
    from moov_backend.api.helper.error_message import moov_errors, not_found_errors
    from moov_backend.api.models import DriverInfo, AdmissionType
    from moov_backend.api.schema import driver_info_schema


class DriverResource(Resource):
    
    @token_required
    @validate_request()
    def put(self):
        json_input = request.get_json()

        keys = [
                    'location_latitude',
                    'location_longitude',
                    'destination_latitude', 
                    'destination_longitude', 
                    'car_slots', 
                    'status',
                    'car_model',
                    'left_image',
                    'right_image',
                    'front_image', 
                    'back_image', 
                    'plate_number',
                    'bank_name',
                    'account_number',
                    'admission_type'
                ]
        if validate_input_data(json_input, keys):
            return validate_input_data(json_input, keys)

        _driver_id = g.current_user.id
        _driver = DriverInfo.query.filter(DriverInfo.driver_id==_driver_id).first()
        if not _driver:
            return moov_errors("Driver does not exist", 404)

        if is_empty_request_fields(json_input):
            return moov_errors("Empty strings are not allowed, exception for image urls", 400)

        for key in json_input.keys():
            if str(key) == "admission_type":
                _admission_type = AdmissionType.query.filter(AdmissionType.admission_type==str(json_input[key])).first()
                if not _admission_type:
                    return moov_errors("Admission type does not exist", 400)
                _driver.__setitem__("admission_type_id", _admission_type.id)

            if str(key) not in ["admission_type"]:
                _driver.__setitem__(key, json_input[key])
        
        _driver.save()
        _data, _ = driver_info_schema.dump(_driver)
        return {
            'status': 'success',
            'data': {
                'driver': _data,
                'message': 'Driver information updated succesfully',
            }
        }, 200
