import os

from flask import g, request, jsonify
from flask_restful import Resource

from ...auth.token import token_required
from ...helper.error_message import moov_errors
from ...models import User
from ...schema import user_signup_schema


class BasicInfoResource(Resource):
    
    @token_required
    def get(self):
        _user_id = g.current_user.id

        _user = User.query.get(_user_id)
        if not _user:
            return moov_errors('User does not exist', 404)

        if (g.current_user.user_type).lower() == "admin":
            return moov_errors('Unauthorized access', 401)

        _data, _ = user_signup_schema.dump(_user)
        _data["user_type"] = _user.user_type.title

        return jsonify({"status": "success",
                        "data": {
                            "message": "Basic information successfully retrieved",
                            "basic_info": _data
                        }
                    })
