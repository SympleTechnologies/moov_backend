import os
import datetime
from os.path import join, dirname
from dotenv import load_dotenv

from sqlalchemy import or_, func
from flask import g, request, jsonify
from flask_restful import Resource
from flask_jwt import jwt

try:
    from ...auth.token import token_required
    from ...auth.validation import (
        validate_request, validate_input_data, validate_empty_string
    )
    from ...helper.common_helper import (
        is_empty_request_fields, remove_unwanted_keys, get_distance
    )
    from ...helper.driver_helper import get_nearest_or_furthest_drivers
    from ...helper.error_message import moov_errors, not_found_errors
    from ...models import User, DriverInfo, AdmissionType
    from ...schema import driver_info_schema, user_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.auth.validation import (
        validate_request, validate_input_data, validate_empty_string
    )
    from moov_backend.api.helper.common_helper import (
        is_empty_request_fields, remove_unwanted_keys, get_distance
    )
    from moov_backend.api.helper.driver_helper import get_nearest_or_furthest_drivers
    from moov_backend.api.helper.error_message import moov_errors, not_found_errors
    from moov_backend.api.models import User, DriverInfo, AdmissionType
    from moov_backend.api.schema import driver_info_schema, user_schema


class DriverResource(Resource):
    
    @token_required
    def get(self):
        _user_id = g.current_user.id
        _user = User.query.get(_user_id)
        if not _user:
            return moov_errors('User does not exist', 404)

        _user_location = request.args.get('user_location')
        _user_destination = request.args.get('user_destination')
        _slots = request.args.get('slots')
        _fare_charge = request.args.get('fare_charge')
        if not _user_location or \
           not _user_destination or \
           not _slots or \
           not _fare_charge or \
           validate_empty_string(_user_location) or \
           validate_empty_string(_user_destination) or \
           validate_empty_string(_slots) or \
           validate_empty_string(_fare_charge):
            return moov_errors("Parameters user_destination, user_location, slots and fare_charge are required", 400)

        try:
            _user_location = _user_location.split(',')
            _user_destination = _user_destination.split(',')

            # confirm if locations contains both latitude and longitude
            if len(_user_location) != 2 or len(_user_destination) != 2: 
                return moov_errors("User destination and location should contain latitude and longitude separated by comma(,)", 400)
            
            # cast the parameters
            _user_location_latitude = float(_user_location[0])
            _user_location_longitude = float(_user_location[1])
            _user_destination_latitude = float(_user_destination[0])
            _user_destination_longitude = float(_user_destination[1])
            _slots = int(_slots)
            _fare_charge = float(_fare_charge)
        except ValueError as error:
            return moov_errors("Parameters should have valid types ({0})".format(error), 400)

        # handles mischief
        if _slots <= 0:
            return moov_errors("Number of slots cannot be less than or equal to zero", 400)

        _user_wallet = _user.wallet_user[0].wallet_amount
        if _user_wallet < _fare_charge:
            return moov_errors("Request denied. Wallet amount not sufficient for this trip", 400)

        _driver = None
        _empty_slot_drivers = []
        _available_slot_drivers = []
        drivers = DriverInfo.query.filter(
                            (DriverInfo.admin_confirmed==True) &
                            (DriverInfo.status==True) &
                            (DriverInfo.available_car_slots>=_slots)
                        ).all()

        # handle case where no driver was found
        if not drivers:
            return moov_errors("No driver available, please try again", 404)

        # sift the result to get empty slot drivers and available drivers
        for driver in drivers:
            _available_slot_drivers.append(driver)
            if driver.on_trip_with == None:
                _empty_slot_drivers.append(driver)

        if _empty_slot_drivers:
            # handle case where there are empty slot drivers
            _driver = _empty_slot_drivers[0]
            _driver.available_car_slots = _driver.car_slots
            _driver.on_trip_with = {}
            _driver.save()
        else:
            # handle case where there are available slot drivers 
            if len(_available_slot_drivers) == 1:
                _driver = _available_slot_drivers[0]
            else:
                nearest_destination_drivers = get_nearest_or_furthest_drivers(
                                                driver_list=_available_slot_drivers,
                                                user_latitude=_user_destination_latitude,
                                                user_longitude=_user_destination_longitude,
                                                number_of_drivers=2,
                                                operation="nearest")
                nearest_location_driver = get_nearest_or_furthest_drivers(
                                                driver_list=nearest_destination_drivers,
                                                user_latitude=_user_location_latitude,
                                                user_longitude=_user_location_longitude,
                                                number_of_drivers=1,
                                                operation="nearest")
                _driver = nearest_location_driver[0]

        _driver.add_to_trip(_driver.driver_id, str(_user.email), _slots)
        _driver_data, _ = driver_info_schema.dump(_driver)
        # append other driver's information from the user's model
        _driver_user_data, _ = user_schema.dump(_driver.driver_information)
        for key in _driver_user_data.keys():
            if key not in ["id", "user_type_id", "user_id", "password", "authorization_code", \
               "authorization_code_status", "reset_password", "number_of_rides", "user_type"]:
                _driver_data[key] = _driver_user_data[key]
            
        return {
            'status': 'success',
            'data': {
                'driver': _driver_data, 
                'message': 'Driver information retrieved succesfully',
            }
        }, 200
    
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

            if str(key) == "car_slots":
                _driver.__setitem__("available_car_slots", json_input["car_slots"])

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
