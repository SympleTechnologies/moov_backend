from flask import request, jsonify, json, Response
from flask_restful import Resource


class RouteResource(Resource):
    
    def get(self):
        return {
            'status': 'success',
            'data': { 'message': "successfully created the route resource" }
        }, 200
