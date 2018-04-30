from flask import g, request, jsonify, json, current_app, url_for, Response
from flask_restful import Resource

try:
    from ...auth.token import token_required
    from ...helper.error_message import moov_errors
    from ...models import SchoolInfo, User
    from ...schema import school_info_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.helper.error_message import moov_errors
    from moov_backend.api.models import SchoolInfo, User
    from moov_backend.api.schema import school_info_schema


class SchoolResource(Resource):
    
    @token_required
    def get(self):
        _user_id = g.current_user.id
        _user = User.query.get(_user_id)
        if not _user:
            return moov_errors('User does not exist', 404)

        _page = request.args.get('page')
        _limit = request.args.get('limit')
        page = int(_page or current_app.config['DEFAULT_PAGE'])
        limit = int(_limit or current_app.config['PAGE_LIMIT'])

        _schools = SchoolInfo.query.order_by(SchoolInfo.name)
        school_count = len(_schools.all())
        _schools = _schools.paginate(
            page=page, per_page=limit, error_out=False)

        schools = []
        for _school in _schools.items:
            _data, _ = school_info_schema.dump(_school)
            schools.append(_data)

        previous_url = None
        next_url = None

        if _schools.has_next:
            next_url = url_for(request.endpoint,
                               limit=limit,
                               page=page+1,
                               _external=True)
        if _schools.has_prev:
            previous_url = url_for(request.endpoint,
                                   limit=limit,
                                   page=page-1,
                                   _external=True)

        return {
            'status': 'success',
            'data': { 
                        'message': 'Schools successfully retrieved',
                        'all_count': school_count,
                        'current_count': len(schools),
                        'schools': schools,
                        'next_url': next_url,
                        'previous_url': previous_url,
                        'current_page': _schools.page,
                        'all_pages': _schools.pages
                    }
        }, 200
