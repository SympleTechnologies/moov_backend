import uuid
from datetime import datetime

try:
    from ..models import FreeRide
except:
    from moov_backend.api.models import FreeRide


# free-ride token generator 
def generate_free_ride_token(user_email):
    payload = "{0} {1}".format(user_email, str(datetime.now))
    free_ride_token = None

    # runs until a unique token is generated
    while not free_ride_token:
        generated_token = uuid.uuid5(uuid.NAMESPACE_DNS, payload)
        _token_found = FreeRide.query.filter(FreeRide.token==generated_token).first()

        if not _token_found:
            free_ride_token = generated_token

    return free_ride_token
