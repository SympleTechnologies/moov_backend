try:
    from .error_message import moov_errors
except ImportError:
    from moov_backend.api.helper.error_message import moov_errors

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
