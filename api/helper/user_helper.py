try:
    from .error_message import moov_errors
    from ..models import User
except ImportError:
    from moov_backend.api.helper.error_message import moov_errors
    from moov_backend.api.models import User

# get any user by email
def get_user(email):
    _user = User.query.filter(User.email==email).first()
    return _user
