from marshmallow import Schema, fields, validate, pre_load, post_dump, validates_schema, ValidationError
from datetime import datetime as dt


def check_unknown_fields(data, original_data, fields):
    unknown = set(original_data) - set(fields)
    if unknown:
        raise ValidationError('{} is not a valid field'.format(), unknown)


class UserSchema(Schema):
    id = fields.Str(dump_only=True)
    user_type = fields.Str(
        required=True,
        errors={
            'required': 'Please provide the user type. It can either be a driver or student',
            'type': 'Invalid type'
        })
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
    authorization_code = fields.Str(errors={'type': 'Invalid type'})
    authorization_code_status = fields.Bool(errors={'type': 'Invalid type'})
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


class TransactionSchema(Schema):
    id = fields.Str(dump_only=True)
    type_of_operation = fields.Str(
            required=True,
            errors={
                'required': 'Please provide a valid type of transaction (transfer, load_wallet or ride_fare).',
                'type': 'Invalid type'
            })
    cost_of_transaction = fields.Float(
            required=True,
            errors={
                'required': 'Please provide the cost of transaction.',
                'type': 'Invalid type'
            })
    transaction_detail = fields.Str(errors={'type': 'Invalid type'})
    type_of_transaction = fields.Str(errors={'type': 'Invalid type'})
    user_amount_before_transaction = fields.Float(errors={'type': 'Invalid type'})
    user_amount_after_transaction = fields.Float(errors={'type': 'Invalid type'})
    sender_amount_before_transaction = fields.Float(errors={'type': 'Invalid type'})
    sender_amount_after_transaction = fields.Float(errors={'type': 'Invalid type'})
    paystack_deduction = fields.Float(errors={'type': 'Invalid type'})
    user_id = fields.Str(errors={'type': 'Invalid type'})
    sender_id = fields.Str(errors={'type': 'Invalid type'})
    user_wallet_id = fields.Str(errors={'type': 'Invalid type'})
    sender_wallet_id = fields.Str(errors={'type': 'Invalid type'})
    transaction_date = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)

    @validates_schema(pass_original=True)
    def unknown_fields(self, data, original_data):
        check_unknown_fields(data, original_data, self.fields)


user_schema = UserSchema()
user_login_schema = UserLoginSchema()
transaction_schema = TransactionSchema()
 