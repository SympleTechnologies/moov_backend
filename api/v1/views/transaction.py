import os

from flask import g, request, jsonify
from flask_restful import Resource

try:
    from ...auth.token import token_required
    from ...auth.validation import validate_request, validate_input_data
    from ...helper.error_message import moov_errors, not_found_errors
    from ...helper.user_helper import get_user
    from ...helper.wallet_helper import get_wallet
    from ...helper.notification_helper import save_notification
    from ...helper.percentage_price_helper import get_percentage_price
    from ...helper.transactions_helper import (
        paystack_deduction_amount, check_transaction_validity
    )
    from ...models import (
        User, Transaction, Wallet, Notification, TransactionType, 
        OperationType
    )
    from ...schema import transaction_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.auth.validation import validate_request, validate_input_data
    from moov_backend.api.helper.error_message import moov_errors, not_found_errors
    from moov_backend.api.helper.user_helper import get_user
    from moov_backend.api.helper.wallet_helper import get_wallet
    from moov_backend.api.helper.notification_helper import save_notification
    from moov_backend.api.helper.percentage_price_helper import get_percentage_price
    from moov_backend.api.helper.transactions_helper import (
        paystack_deduction_amount, check_transaction_validity
    )
    from moov_backend.api.models import (
        User, Transaction, Wallet, Notification, TransactionType, 
        OperationType
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

        moov_email = os.environ.get("MOOV_EMAIL")
        moov_user = User.query.filter(User.email==moov_email).first()
        if not moov_user:
            return not_found_errors(moov_email)

        # case load_wallet
        if str(json_input['type_of_operation']).lower() == 'load_wallet':
            _receiver_wallet = Wallet.query.filter(Wallet.user_id==_current_user_id).first()
            cost_of_transaction = json_input["cost_of_transaction"]

            message = "Cost of transaction cannot be a negative value"
            if check_transaction_validity(cost_of_transaction, message):
                return check_transaction_validity(cost_of_transaction, message)
            
            paystack_deduction = paystack_deduction_amount(cost_of_transaction)
            receiver_amount_before_transaction = _receiver_wallet.wallet_amount
            new_cost_of_transaction = cost_of_transaction - paystack_deduction
            receiver_amount_after_transaction = receiver_amount_before_transaction + new_cost_of_transaction
            receiver_id = _current_user_id
            receiver_wallet_id = _receiver_wallet.id
            transaction_detail = "{0}'s wallet has been credited with {1} with a paystack deduction of {2}".format(_current_user.firstname, new_cost_of_transaction, paystack_deduction)

            new_transaction = Transaction(
                transaction_detail= transaction_detail,
                type_of_operation= OperationType.wallet_type,
                type_of_transaction= TransactionType.credit_type,
                cost_of_transaction= cost_of_transaction,
                receiver_amount_before_transaction= receiver_amount_before_transaction,
                receiver_amount_after_transaction= receiver_amount_after_transaction,
                paystack_deduction= paystack_deduction,
                receiver_id= receiver_id,
                receiver_wallet_id= receiver_wallet_id
            )
            new_transaction.save()

            _receiver_wallet.wallet_amount = receiver_amount_after_transaction
            _receiver_wallet.save()

            notification_message = "Your wallet has been credited with N{0} with a transaction charge of N{1}".format(new_cost_of_transaction, paystack_deduction)
            save_notification(recipient_id=receiver_id, sender_id=moov_user.id, message=notification_message)

            _data, _ = transaction_schema.dump(new_transaction)
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
            new_transaction = {}

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
                receiver_amount_after_transaction = _receiver_wallet.wallet_amount + cost_of_transaction
                sender_amount_after_transaction = _sender_wallet.wallet_amount - cost_of_transaction - transfer_charge
                transaction_detail = "{0} transfered N{1} to {2} with a transaction charge of {3}".format(_sender.email, cost_of_transaction, _receiver.email, transfer_charge)

                if check_transaction_validity(sender_amount_after_transaction, message):
                  return check_transaction_validity(sender_amount_after_transaction, message)

                moov_wallet = get_wallet(email=moov_email)
                if not moov_wallet:
                    return not_found_errors(moov_email)

                new_transaction = Transaction(
                    transaction_detail= transaction_detail,
                    type_of_operation= OperationType.transfer_type,
                    type_of_transaction= TransactionType.both_types,
                    cost_of_transaction= cost_of_transaction,
                    receiver_amount_before_transaction= receiver_amount_before_transaction,
                    receiver_amount_after_transaction= receiver_amount_after_transaction,
                    sender_amount_before_transaction= sender_amount_before_transaction,
                    sender_amount_after_transaction= sender_amount_after_transaction,
                    receiver_id= _receiver.id,
                    sender_id= _sender.id,
                    receiver_wallet_id= _receiver_wallet.id,
                    sender_wallet_id= _sender_wallet.id
                )
                new_transaction.save()

                # wallet updates
                _receiver_wallet.wallet_amount = receiver_amount_after_transaction
                _sender_wallet.wallet_amount = sender_amount_after_transaction
                moov_wallet.wallet_amount += transfer_charge
                _receiver_wallet.save()
                _sender_wallet.save()
                moov_wallet.save()

                notification_user_sender_message = "Your wallet has been debited with N{0}, with a transaction charge of N{1} by {2}".format(cost_of_transaction, transfer_charge, "MOOV")
                notification_user_receiver_message = "Your wallet has been credited with N{0} by {1}".format(cost_of_transaction, (str(_sender.firstname)).title())
                save_notification(recipient_id=_sender.id, sender_id=moov_user.id, message=notification_user_sender_message)
                save_notification(recipient_id=_receiver.id, sender_id=moov_user.id, message=notification_user_receiver_message)

                _data, _ = transaction_schema.dump(new_transaction)
                return {
                        'status': 'success',
                        'data': {
                            'transaction': _data,
                            'message': "Transaction succesful"
                        }
                }, 201
                 
            # case ride_fare
            if str(json_input['type_of_operation']).lower() == 'ride_fare':
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

                transaction_detail = "{0} paid N{1} ride fare to {2}".format(_sender.email, cost_of_transaction, _receiver.email)
                driver_percentage_price_info = get_percentage_price(title="driver")
                school_percentage_price_info = get_percentage_price(title=school_email)
                car_owner_percentage_price_info = get_percentage_price(title=car_owner_email)

                if not car_owner_percentage_price_info or not school_percentage_price_info:
                    return moov_errors("Percentage price was not set for the school or car_owner ({0}, {1})".format(school_email, car_owner_email), 400)

                driver_amount = driver_percentage_price_info.price * cost_of_transaction
                receiver_amount_after_transaction = receiver_amount_before_transaction + driver_amount
                school_wallet_amount = school_percentage_price_info.price * cost_of_transaction
                car_owner_wallet_amount = car_owner_percentage_price_info.price * cost_of_transaction
                moov_wallet_amount = cost_of_transaction - (driver_amount + school_wallet_amount + car_owner_wallet_amount)
                
                new_transaction = Transaction(
                    transaction_detail= transaction_detail,
                    type_of_operation= OperationType.ride_type,
                    type_of_transaction= TransactionType.both_types,
                    cost_of_transaction= cost_of_transaction,
                    receiver_amount_before_transaction= receiver_amount_before_transaction,
                    receiver_amount_after_transaction= receiver_amount_after_transaction,
                    sender_amount_before_transaction= sender_amount_before_transaction,
                    sender_amount_after_transaction= sender_amount_after_transaction,
                    receiver_id= _receiver.id,
                    sender_id= _sender.id,
                    receiver_wallet_id= _receiver_wallet.id,
                    sender_wallet_id= _sender_wallet.id
                )
                new_transaction.save()

                # wallet_updates
                moov_wallet.wallet_amount += moov_wallet_amount
                school_wallet.wallet_amount += school_wallet_amount
                car_owner_wallet.wallet_amount += car_owner_wallet_amount
                _receiver_wallet.wallet_amount = receiver_amount_after_transaction
                _sender_wallet.wallet_amount = sender_amount_after_transaction
                moov_wallet.save()
                school_wallet.save()
                car_owner_wallet.save()
                _receiver_wallet.save()
                _sender_wallet.save()

                notification_user_sender_message = "Your wallet has been debited with N{0} for your ride fare with {1}".format(cost_of_transaction, (str(_receiver.firstname)).title())
                notification_user_receiver_message = "Your wallet has been credited with N{0} by {1}".format(driver_amount, (str(_sender.firstname)).title())
                save_notification(recipient_id=_sender.id, sender_id=moov_user.id, message=notification_user_sender_message)
                save_notification(recipient_id=_receiver.id, sender_id=moov_user.id, message=notification_user_receiver_message)

                _data, _ = transaction_schema.dump(new_transaction)
                return {
                        'status': 'success',
                        'data': {
                            'transaction': _data,
                            'message': "Transaction succesful"
                        }
                    }, 201

        # cases that don't meet the required condition
        return moov_errors("Transaction denied", 400) 
