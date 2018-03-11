from flask import request, jsonify, json, Response
from flask_restful import Resource

from ...auth.token import token_required


class FreeRideResource(Resource):
    
    @token_required
    def post(self):
        pass
