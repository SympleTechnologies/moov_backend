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
    from ...helper.transactions_helper import (
        paystack_deduction_amount, check_transaction_validity
    )
    from ...models import (
        User, Transaction, Wallet, Notification, TransactionType, OperationType
    )
    from ...schema import transaction_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.auth.validation import validate_request, validate_input_data
    from moov_backend.api.helper.error_message import moov_errors, not_found_errors
    from moov_backend.api.helper.user_helper import get_user
    from moov_backend.api.helper.wallet_helper import get_wallet
    from moov_backend.api.helper.notification_helper import save_notification
    from moov_backend.api.helper.transactions_helper import (
        paystack_deduction_amount, check_transaction_validity
    )
    from moov_backend.api.models import (
        User, Transaction, Wallet, Notification, TransactionType, OperationType
    )
    from moov_backend.api.schema import transaction_schema


class TransactionResource(Resource):
    
    @token_required
    @validate_request()
    def post(self):
        json_input = request.get_json()
        
        keys = ['type_of_operation', 'cost_of_transaction', 'user_id']

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

        moov_email = "moov@email.com"
        moov_user = User.query.filter(User.email==moov_email).first()
        if not moov_user:
            return not_found_errors("moov@email.com")

        # case load_wallet
        if str(json_input['type_of_operation']).lower() == 'load_wallet':
            _current_user_wallet = Wallet.query.filter(Wallet.user_id==_current_user_id).first()
            cost_of_transaction = json_input["cost_of_transaction"]

            message = "Cost of transaction cannot be a negative value"
            if check_transaction_validity(cost_of_transaction, message):
                return check_transaction_validity(cost_of_transaction, message)
            
            paystack_deduction = paystack_deduction_amount(cost_of_transaction)
            user_amount_before_transaction = _current_user_wallet.wallet_amount
            new_cost_of_transaction = cost_of_transaction - paystack_deduction
            user_amount_after_transaction = user_amount_before_transaction + new_cost_of_transaction
            user_id = _current_user_id
            user_wallet_id = _current_user_wallet.id
            transaction_detail = "{0}'s wallet has been credited with {1} with a paystack deduction of {2}".format(_current_user.firstname, new_cost_of_transaction, paystack_deduction)

            new_transaction = Transaction(
                transaction_detail= transaction_detail,
                type_of_operation= OperationType.wallet_type,
                type_of_transaction= TransactionType.credit_type,
                cost_of_transaction= cost_of_transaction,
                user_amount_before_transaction= user_amount_before_transaction,
                user_amount_after_transaction= user_amount_after_transaction,
                paystack_deduction= paystack_deduction,
                user_id= user_id,
                user_wallet_id= user_wallet_id
            )
            new_transaction.save()

            _current_user_wallet.wallet_amount = user_amount_after_transaction
            _current_user_wallet.save()

            notification_message = "Your wallet has been credited with N{0} with a transaction charge of N{1}".format(new_cost_of_transaction, paystack_deduction)
            save_notification(recipient_id=user_id, sender_id=moov_user.id, message=notification_message)

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
            _user_id = json_input['user_id']
            _sender_id = _current_user_id
            _sender = _current_user
            _user = User.query.filter(User.email==_user_id).first()

            if not _user:
                return moov_errors("User does not exist", 404)
            if str(_user.user_type.title) == "admin":
                return moov_errors("Unauthorized access", 401) 
            

            _user_wallet = Wallet.query.filter(Wallet.user_id==_user.id).first()
            _sender_wallet = Wallet.query.filter(Wallet.user_id==_sender_id).first()

            message = "Cost of transaction cannot be a negative value"
            if check_transaction_validity(cost_of_transaction, message):
                return check_transaction_validity(cost_of_transaction, message)

            user_amount_before_transaction = _user_wallet.wallet_amount
            sender_amount_before_transaction = _sender_wallet.wallet_amount
            sender_amount_after_transaction = _sender_wallet.wallet_amount - cost_of_transaction

            message = "Sorry, you cannot transfer more than your wallet amount"
            if check_transaction_validity(sender_amount_after_transaction, message):
                return check_transaction_validity(sender_amount_after_transaction, message)

            # case transfer
            if str(json_input['type_of_operation']).lower() == 'transfer':
                transaction_detail = "{0} transfered N{1} to {2}".format(_sender.email, cost_of_transaction, _user.email)
                transfer_charge = 0.02 * cost_of_transaction
                user_amount_after_transaction = _user_wallet.wallet_amount + cost_of_transaction
                sender_amount_after_transaction = _sender_wallet.wallet_amount - cost_of_transaction - transfer_charge

                if check_transaction_validity(sender_amount_after_transaction, message):
                  return check_transaction_validity(sender_amount_after_transaction, message)

                moov_wallet = get_wallet(email="moov@email.com")
                if not moov_wallet:
                    return not_found_errors("moov@email.com")

                new_transaction = Transaction(
                    transaction_detail= transaction_detail,
                    type_of_operation= OperationType.transfer_type,
                    type_of_transaction= TransactionType.both_types,
                    cost_of_transaction= cost_of_transaction,
                    user_amount_before_transaction= user_amount_before_transaction,
                    user_amount_after_transaction= user_amount_after_transaction,
                    sender_amount_before_transaction= sender_amount_before_transaction,
                    sender_amount_after_transaction= sender_amount_after_transaction,
                    user_id= _user.id,
                    sender_id= _sender.id,
                    user_wallet_id= _user_wallet.id,
                    sender_wallet_id= _sender_wallet.id
                )
                new_transaction.save()

                # wallet updates
                wallet_message = "{0} transfered {1} to {2} with a charge of {3}".format(_sender.email, sender_amount_after_transaction, _user.email, transfer_charge)
                _user_wallet.wallet_amount = user_amount_after_transaction
                _user_wallet.message = wallet_message
                _sender_wallet.wallet_amount = sender_amount_after_transaction
                _sender_wallet.message = wallet_message
                wallet_message = "Transfer charge for transaction: {0}".format(new_transaction.id)
                moov_wallet.wallet_amount += transfer_charge
                moov_wallet.message = wallet_message
                _user_wallet.save()
                _sender_wallet.save()
                moov_wallet.save()

                notification_user_sender_message = "Your wallet has been debited with N{0}, with a transaction charge of N{1} by {2}".format(cost_of_transaction, transfer_charge, "MOOV")
                notification_user_receiver_message = "Your wallet has been credited with N{0} by {1}".format(cost_of_transaction, (str(_sender.firstname)).title())
                save_notification(recipient_id=_sender.id, sender_id=moov_user.id, message=notification_user_sender_message)
                save_notification(recipient_id=_user.id, sender_id=moov_user.id, message=notification_user_receiver_message)
                 
            # case ride_fare
            if str(json_input['type_of_operation']).lower() == 'ride_fare':
                moov_wallet = get_wallet(email="moov@email.com")
                school_wallet = get_wallet(email="school@email.com")
                car_owner_wallet = get_wallet(email="car_owner@email.com")

                if not moov_wallet:
                    return not_found_errors("moov@email.com")
                if not school_wallet:
                    return not_found_errors("school@email.com")
                if not car_owner_wallet:
                    return not_found_errors("car_owner@email.com")

                transaction_detail = "{0} paid N{1} ride fare to {2}".format(_sender.email, cost_of_transaction, _user.email)
                driver_amount = 0.2 * cost_of_transaction
                user_amount_after_transaction = user_amount_before_transaction + driver_amount
                school_wallet_amount = 0.4 * cost_of_transaction
                car_owner_wallet_amount = 0 * cost_of_transaction
                moov_wallet_amount = cost_of_transaction - (driver_amount + school_wallet_amount + car_owner_wallet_amount)
                
                new_transaction = Transaction(
                    transaction_detail= transaction_detail,
                    type_of_operation= OperationType.ride_type,
                    type_of_transaction= TransactionType.both_types,
                    cost_of_transaction= cost_of_transaction,
                    user_amount_before_transaction= user_amount_before_transaction,
                    user_amount_after_transaction= user_amount_after_transaction,
                    sender_amount_before_transaction= sender_amount_before_transaction,
                    sender_amount_after_transaction= sender_amount_after_transaction,
                    user_id= _user.id,
                    sender_id= _sender.id,
                    user_wallet_id= _user_wallet.id,
                    sender_wallet_id= _sender_wallet.id
                )
                new_transaction.save()

                # wallet_updates
                wallet_message = "Percentage share from transaction: {0}".format(new_transaction.id)
                moov_wallet.wallet_amount += moov_wallet_amount
                moov_wallet.message = wallet_message
                school_wallet.wallet_amount += school_wallet_amount
                school_wallet.message = wallet_message
                car_owner_wallet.wallet_amount += car_owner_wallet_amount
                car_owner_wallet.message = wallet_message
                _user_wallet.wallet_amount = user_amount_after_transaction
                _user_wallet.message = "Ride fare with {0}".format(_sender.email)
                _sender_wallet.wallet_amount = sender_amount_after_transaction
                _sender_wallet.message = "Ride fare with {0}".format(_user.email)
                moov_wallet.save()
                school_wallet.save()
                car_owner_wallet.save()
                _user_wallet.save()
                _sender_wallet.save()

                notification_user_sender_message = "Your wallet has been debited with N{0} for your ride fare with {1}".format(cost_of_transaction, (str(_user.firstname)).title())
                notification_user_receiver_message = "Your wallet has been credited with N{0} by {1}".format(driver_amount, (str(_sender.firstname)).title())
                save_notification(recipient_id=_sender.id, sender_id=moov_user.id, message=notification_user_sender_message)
                save_notification(recipient_id=_user.id, sender_id=moov_user.id, message=notification_user_receiver_message)

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
