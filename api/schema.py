from marshmallow import Schema, fields, validate, pre_load, post_dump, validates_schema, ValidationError
from datetime import datetime as dt


def check_unknown_fields(data, original_data, fields):
    unknown = set(original_data) - set(fields)
    if unknown:
        raise ValidationError('{} is not a valid field'.format(), unknown)


class UserSignupSchema(Schema):
    id = fields.Str(dump_only=True)
    firstname = fields.Str(
        required=True,
        errors={
            'required': 'Please provide your firstname.',
            'type': 'Invalid type'
        })
    lastname = fields.Str(
        required=True,
        errors={
            'required': 'Please provide your lastname.',
            'type': 'Invalid type'
        })
    email = fields.Str(
        required=True,
        errors={
            'required': 'Please provide a valid email.',
            'type': 'Invalid type'
        })
    image_url = fields.Str(errors={'type': 'Invalid type'})
    created_at = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)

    @validates_schema(pass_original=True)
    def unknown_fields(self, data, original_data):
        check_unknown_fields(data, original_data, self.fields)


class UserLoginSchema(Schema):
    id = fields.Str(dump_only=True)
    email = fields.Str(
        required=True,
        errors={
            'required': 'Please provide a valid email.',
            'type': 'Invalid type'
        })

    @validates_schema(pass_original=True)
    def unknown_fields(self, data, original_data):
        check_unknown_fields(data, original_data, self.fields)


user_signup_schema = UserSignupSchema()
user_login_schema = UserLoginSchema()
