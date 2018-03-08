
# imports
from datetime import datetime, timedelta

from sqlalchemy import desc, and_

try:
    from .error_message import moov_errors
    from ..helper.notification_helper import save_notification
    from ..schema import transaction_schema
    from ..models import (
        Wallet, Icon, Transaction, OperationType, TransactionType
    )
except ImportError:
    from moov_backend.api.helper.error_message import moov_errors
    from moov_backend.api.helper.notification_helper import save_notification
    from moov_backend.api.schema import transaction_schema
    from moov_backend.api.models import (
        Wallet, Icon, Transaction, OperationType, TransactionType
    )

# load-wallet operation function
def load_wallet_operation(cost_of_transaction, _current_user, _current_user_id, moov_user):
    _receiver_wallet = Wallet.query.filter(Wallet.user_id==_current_user_id).first()
    
    paystack_deduction = paystack_deduction_amount(cost_of_transaction)
    receiver_amount_before_transaction = _receiver_wallet.wallet_amount
    new_cost_of_transaction = cost_of_transaction - paystack_deduction
    receiver_amount_after_transaction = receiver_amount_before_transaction + new_cost_of_transaction
    receiver_id = _current_user_id
    receiver_wallet_id = _receiver_wallet.id
    transaction_detail = "{0}'s wallet has been credited with {1} with a paystack deduction of {2}".format(_current_user.firstname, new_cost_of_transaction, paystack_deduction)

    _receiver_wallet.wallet_amount = receiver_amount_after_transaction
    _receiver_wallet.save()

    transaction_icon = Icon.query.filter(Icon.operation_type=="load_wallet_operation").first()
    if transaction_icon:
        _transaction_icon_id = transaction_icon.id

    notification_message = "Your wallet has been credited with N{0} with a transaction charge of N{1}".format(new_cost_of_transaction, paystack_deduction)
    save_notification(
            recipient_id=receiver_id, 
            sender_id=moov_user.id, 
            message=notification_message, 
            transaction_icon_id=_transaction_icon_id
        )
    
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
    return transaction_schema.dump(new_transaction)

# transfer operation function
def transfer_operation(_sender, _receiver, _sender_wallet, _receiver_wallet, 
    moov_wallet, cost_of_transaction, transfer_charge, sender_amount_before_transaction,
    receiver_amount_before_transaction, sender_amount_after_transaction, moov_user):
    receiver_amount_after_transaction = _receiver_wallet.wallet_amount + cost_of_transaction
    transaction_detail = "{0} transfered N{1} to {2} with a transaction charge of {3}".format(_sender.email, cost_of_transaction, _receiver.email, transfer_charge)

    # wallet updates
    # DO NOT CHANGE THE SEQUENCE OF THE CODE BELOW
    # IT PREVENTS HACK
    _sender_wallet.wallet_amount = sender_amount_after_transaction
    _receiver_wallet.wallet_amount = receiver_amount_after_transaction
    moov_wallet.wallet_amount += transfer_charge
    _sender_wallet.save()
    _receiver_wallet.save()
    moov_wallet.save()

    transaction_icon = Icon.query.filter(Icon.operation_type=="transfer_operation").first()
    if transaction_icon:
        _transaction_icon_id = transaction_icon.id

    notification_user_sender_message = "Your wallet has been debited with N{0}, with a transaction charge of N{1} by {2}".format(cost_of_transaction, transfer_charge, "MOOV")
    notification_user_receiver_message = "Your wallet has been credited with N{0} by {1}".format(cost_of_transaction, (str(_sender.firstname)).title())
    save_notification(
            recipient_id=_sender.id, 
            sender_id=moov_user.id, 
            message=notification_user_sender_message, 
            transaction_icon_id=_transaction_icon_id
        )
    save_notification(
            recipient_id=_receiver.id, 
            sender_id=moov_user.id, 
            message=notification_user_receiver_message, 
            transaction_icon_id=_transaction_icon_id
        )

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
    return transaction_schema.dump(new_transaction)

# ride-fare operation function
def ride_fare_operation(_sender, _receiver, driver_percentage_price_info, 
    school_percentage_price_info, car_owner_percentage_price_info, cost_of_transaction,
    receiver_amount_before_transaction, sender_amount_before_transaction, sender_amount_after_transaction, moov_wallet, school_wallet, car_owner_wallet, 
    _sender_wallet, _receiver_wallet, moov_user):
    transaction_detail = "{0} paid N{1} ride fare to {2}".format(_sender.email, cost_of_transaction, _receiver.email)

    driver_amount = driver_percentage_price_info.price * cost_of_transaction
    receiver_amount_after_transaction = receiver_amount_before_transaction + driver_amount
    school_wallet_amount = school_percentage_price_info.price * cost_of_transaction
    car_owner_wallet_amount = car_owner_percentage_price_info.price * cost_of_transaction
    moov_wallet_amount = cost_of_transaction - (driver_amount + school_wallet_amount + car_owner_wallet_amount)

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

    transaction_icon = Icon.query.filter(Icon.operation_type=="ride_operation").first()
    if transaction_icon:
        _transaction_icon_id = transaction_icon.id
    
    notification_user_sender_message = "Your wallet has been debited with N{0} for your ride fare with {1}".format(cost_of_transaction, (str(_receiver.firstname)).title())
    notification_user_receiver_message = "Your wallet has been credited with N{0} by {1}".format(driver_amount, (str(_sender.firstname)).title())
    save_notification(
            recipient_id=_sender.id, 
            sender_id=moov_user.id, 
            message=notification_user_sender_message, 
            transaction_icon_id=_transaction_icon_id
        )
    save_notification(
            recipient_id=_receiver.id, 
            sender_id=moov_user.id, 
            message=notification_user_receiver_message, 
            transaction_icon_id=_transaction_icon_id
        )

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
    return transaction_schema.dump(new_transaction)

# paystack deduction calculation
def paystack_deduction_amount(cost_of_transaction):
    if cost_of_transaction < 2500:
        # percentage taken from paystack is 1.5%
        return cost_of_transaction * 0.015

    # percentage taken from paystack for cost equal 
    # or over 2500 is 1.5% +100
    return (cost_of_transaction * 0.015) + 100

# check transaction validity
def check_transaction_validity(amount, message):
    if amount < 0:
        return moov_errors(message, 400)

def check_past_week_rides(user_id):
    day = datetime.today() - timedelta(days=7)
    past_week_rides = Transaction(desc(and_(
                            Transaction.sender_id==user_id,
                            Transaction.type_of_operation=="ride_type",
                            Transaction.transaction_date>=day
                        ))).limit(20).all()
    import pdb; pdb.set_trace()
    return len(past_week_rides)
