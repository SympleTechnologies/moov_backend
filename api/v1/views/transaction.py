import os
from datetime import datetime

from flask import g, request, jsonify
from flask_restful import Resource

try:
    from ...auth.token import token_required
    from ...auth.validation import validate_request, validate_input_data
    from ...generator.free_ride_token_generator import generate_free_ride_token
    from ...helper.error_message import moov_errors, not_found_errors
    from ...helper.user_helper import get_user
    from ...helper.wallet_helper import get_wallet
    from ...helper.percentage_price_helper import get_percentage_price
    from ...helper.notification_helper import save_notification
    from ...helper.free_ride_helper import get_free_ride_token, save_free_ride_token
    from ...helper.transactions_helper import (
        paystack_deduction_amount, check_transaction_validity, load_wallet_operation,
        ride_fare_operation, transfer_operation
    )
    from ...models import (
        User, Transaction, Wallet, Icon
    )
    from ...schema import transaction_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.auth.validation import validate_request, validate_input_data
    from moov_backend.api.helper.error_message import moov_errors, not_found_errors
    from moov_backend.api.helper.user_helper import get_user
    from moov_backend.api.helper.wallet_helper import get_wallet
    from moov_backend.api.helper.percentage_price_helper import get_percentage_price
    from moov_backend.api.helper.notification_helper import save_notification
    from moov_backend.api.helper.free_ride_helper import get_free_ride_token, save_free_ride_token
    from moov_backend.api.helper.transactions_helper import (
        paystack_deduction_amount, check_transaction_validity, load_wallet_operation,
        ride_fare_operation, transfer_operation
    )
    from moov_backend.api.models import (
        User, Transaction, Wallet, Icon
    )
    from moov_backend.api.schema import transaction_schema


class TransactionResource(Resource):
    
    @token_required
    @validate_request()
    def post(self):
        json_input = request.get_json()
        
        keys = ['type_of_operation', 'cost_of_transaction', 'user_id', 'school_email', 'car_owner_email']

        _transaction = {}
        if validate_input_data(json_input, keys, _transaction):
            return validate_input_data(json_input, keys, _transaction)

        data, errors = transaction_schema.load(json_input)
        if errors:
            return moov_errors(errors, 422)

        # establishing the _current_user is valid and not an admin
        _current_user_id = g.current_user.id

        _current_user = User.query.get(_current_user_id)
        if not _current_user:
            return moov_errors('User does not exist', 404)

        _current_user_type = (_current_user.user_type.title).lower()
        if _current_user_type == "admin":
            return moov_errors('Unauthorized access', 401)

        _transaction_icon = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973461_1280.png"

        moov_email = os.environ.get("MOOV_EMAIL")
        moov_user = User.query.filter(User.email==moov_email).first()
        if not moov_user:
            return not_found_errors(moov_email)

        # case load_wallet
        if str(json_input['type_of_operation']).lower() == 'load_wallet':
            cost_of_transaction = json_input["cost_of_transaction"]

            message = "Cost of transaction cannot be a negative value"
            if check_transaction_validity(cost_of_transaction, message):
                return check_transaction_validity(cost_of_transaction, message)
            
            _data, _ = load_wallet_operation(cost_of_transaction, _current_user, _current_user_id, moov_user)
            return {
                    'status': 'success',
                    'data': {
                        'transaction': _data,
                        'message': "Transaction succesful"
                    }
                }, 201

        # case ride_fare and transfer
        if ('user_id') in json_input:
            cost_of_transaction = json_input["cost_of_transaction"]
            _receiver_id = json_input['user_id']
            _sender_id = _current_user_id
            _sender = _current_user
            _receiver = User.query.filter(User.email==_receiver_id).first()

            if not _receiver:
                return moov_errors("User does not exist", 404)
            if str(_receiver.user_type.title) == "admin":
                return moov_errors("Unauthorized access", 401) 
            

            _receiver_wallet = Wallet.query.filter(Wallet.user_id==_receiver.id).first()
            _sender_wallet = Wallet.query.filter(Wallet.user_id==_sender_id).first()

            message = "Cost of transaction cannot be a negative value"
            if check_transaction_validity(cost_of_transaction, message):
                return check_transaction_validity(cost_of_transaction, message)

            receiver_amount_before_transaction = _receiver_wallet.wallet_amount
            sender_amount_before_transaction = _sender_wallet.wallet_amount
            sender_amount_after_transaction = _sender_wallet.wallet_amount - cost_of_transaction

            message = "Sorry, you cannot transfer more than your wallet amount"
            if check_transaction_validity(sender_amount_after_transaction, message):
                return check_transaction_validity(sender_amount_after_transaction, message)

            # case transfer
            if str(json_input['type_of_operation']).lower() == 'transfer':
                if str(_receiver.id) == str(_sender_id):
                    return moov_errors("Unauthorized. A user cannot transfer to him/herself", 401)
                
                transfer_percentage_price = (get_percentage_price(title="transfer")).price
                transfer_charge = transfer_percentage_price * cost_of_transaction
                sender_amount_after_transaction = _sender_wallet.wallet_amount - cost_of_transaction - transfer_charge

                if check_transaction_validity(sender_amount_after_transaction, message):
                  return check_transaction_validity(sender_amount_after_transaction, message)

                moov_wallet = get_wallet(email=moov_email)
                if not moov_wallet:
                    return not_found_errors(moov_email)

                _data, _ = transfer_operation(
                                _sender, 
                                _receiver, 
                                _sender_wallet, 
                                _receiver_wallet, 
                                moov_wallet, 
                                cost_of_transaction, 
                                transfer_charge, 
                                sender_amount_before_transaction, 
                                receiver_amount_before_transaction, 
                                sender_amount_after_transaction, 
                                moov_user
                            )
                return {
                        'status': 'success',
                        'data': {
                            'transaction': _data,
                            'message': "Transaction succesful"
                        }
                }, 201
                 
            # case ride_fare
            if str(json_input['type_of_operation']).lower() == 'ride_fare':
                # increments the number of rides taken by a user
                _sender.number_of_rides += 1

                if "school_email" not in json_input:
                    return moov_errors("school_email field is compulsory for ride fare", 400)

                if not get_user(json_input["school_email"]):
                    return not_found_errors(json_input["school_email"])

                school_email = json_input["school_email"]
                car_owner_email = os.environ.get("CAR_OWNER_EMAIL") if ("car_owner" not in json_input) else json_input["car_owner"]
                if not get_user(car_owner_email):
                    return not_found_errors(car_owner_email)

                moov_wallet = get_wallet(email=moov_email)
                school_wallet = get_wallet(email=school_email)
                car_owner_wallet = get_wallet(email=car_owner_email)

                if not moov_wallet:
                    return not_found_errors(moov_email)
                if not school_wallet:
                    return not_found_errors(school_email)
                if not car_owner_wallet:
                    return not_found_errors(car_owner_email)

                driver_percentage_price_info = get_percentage_price(title="driver")
                school_percentage_price_info = get_percentage_price(title=school_email)
                car_owner_percentage_price_info = get_percentage_price(title=car_owner_email)

                if not car_owner_percentage_price_info or not school_percentage_price_info:
                    return moov_errors("Percentage price was not set for the school or car_owner ({0}, {1})".format(school_email, car_owner_email), 400)

                # free ride generation
                free_ride_token = get_free_ride_token(_sender)
                if free_ride_token:
                    free_ride_description = "Token generated for {0} on the {1} for ride number {2}".format(
                                                _sender.email, str(datetime.now()), _sender.number_of_rides
                                            )
                    save_free_ride_token(
                        token=free_ride_token, 
                        description=free_ride_description, 
                        user_id=_sender_id
                    )

                    free_ride_icon = Icon.query.filter(Icon.operation_type=="free_ride_operation").first()
                    free_ride_notification_message = "You have earned a free ride token '{0}'".format(free_ride_token)
                    save_notification(
                        recipient_id=_sender_id, 
                        sender_id=moov_user.id, 
                        message=free_ride_notification_message, 
                        transaction_icon_id=free_ride_icon.id
                    )
                
                _data, _ = ride_fare_operation(
                                _sender, 
                                _receiver, 
                                driver_percentage_price_info, 
                                school_percentage_price_info, 
                                car_owner_percentage_price_info, 
                                cost_of_transaction, 
                                receiver_amount_before_transaction, 
                                sender_amount_before_transaction, 
                                sender_amount_after_transaction, 
                                moov_wallet, 
                                school_wallet, 
                                car_owner_wallet, 
                                _sender_wallet, 
                                _receiver_wallet, 
                                moov_user
                            )
                _data["free_ride_token"] = free_ride_token
                return {
                        'status': 'success',
                        'data': {
                            'transaction': _data,
                            'message': "Transaction succesful"
                        }
                    }, 201

        # cases that don't meet the required condition
        return moov_errors("Transaction denied", 400) 

class AllTransactionsResource(Resource):
    
    def get(self):
        pass
