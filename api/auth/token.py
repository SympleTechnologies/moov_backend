from functools import wraps

from flask import g, request, jsonify
from flask_jwt import jwt


# authorization decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # check that the Authorization header is set
        authorization_token = request.headers.get('Authorization')
        if not authorization_token:
            response = jsonify({
                "status": "fail",
                "data": {
                    "message": "Bad request. Header does not contain"
                            " authorization token"
                }
            })
            response.status_code = 400
            return response

        # validates the word bearer is in the token
        if 'bearer ' not in authorization_token.lower():
            response = jsonify({
                "status": "fail",
                "data": {
                    "message": "Invalid Token. The token should begin with"
                            " 'Bearer '"
                }
            })
            response.status_code = 400
            return response

        unauthorized_response = jsonify({
            "status": "fail",
            "data": {
                "message": "Unauthorized. The authorization token supplied"
                        " is invalid"
            }
        })
        unauthorized_response.status_code = 401
        expired_response = jsonify({
            "status": "fail",
            "data": {
                "message": "The authorization token supplied is expired"
            }
        })
        expired_response.status_code = 401

        try:
            # extracts token by removing bearer
            authorization_token = authorization_token.split(' ')[1]

            # decode token
            payload = jwt.decode(authorization_token, 'secret',
                                 options={"verify_signature": False})
        except jwt.ExpiredSignatureError:
            return expired_response
        except jwt.InvalidTokenError:
            return unauthorized_response

        # confirm that payload has required keys
        if ("id", "exp") not in payload.keys():
            return unauthorized_response
        else:
            # set current user in flask global variable, g
            g.current_user = payload["id"]

            # now return wrapped function
            return f(*args, **kwargs)
    return decorated
