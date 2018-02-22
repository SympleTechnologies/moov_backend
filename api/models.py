# models
import os
import json
import enum

from alembic import op
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref, relationship

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.types import JSON, TEXT, TypeDecorator
from sqlalchemy import event
from datetime import datetime

try:
    from generator.id_generator import PushID
except ImportError:
    from moov_backend.api.generator.id_generator import PushID

def to_camel_case(snake_str):
    title_str = snake_str.title().replace("_", "")
    return title_str[0].lower() + title_str[1:]


class StringyJSON(TypeDecorator):
    """Stores and retrieves JSON as TEXT."""

    impl = TEXT

    def process_bind_param(self, value, dialect):
        """Map value into json data."""
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        """Map json data to python dictionary."""
        if value is not None:
            value = json.loads(value)
        return value


# TypeEngine.with_variant says "use StringyJSON instead when
# connecting to 'sqlite'"
MagicJSON = JSON().with_variant(StringyJSON, 'sqlite')

type_map = {'sqlite': MagicJSON, 'postgresql': JSON}
json_type = type_map[os.getenv("DB_TYPE")]

db = SQLAlchemy()

class ModelViewsMix(object):

    def serialize(self):
        return {to_camel_case(column.name): getattr(self, column.name)
                for column in self.__table__.columns}

    def save(self):
        """Saves an instance of the model to the database."""
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except SQLAlchemyError as error:
            db.session.rollback()
            return error
    
    def delete(self):
        """Delete an instance of the model from the database."""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except SQLAlchemyError as error:
            db.session.rollback()
            return error


class OperationType(enum.Enum):
    transfer_type = "transfer"
    wallet_type = "load_wallet"
    ride_type = "ride_fare"


class TransactionType(enum.Enum):
    debit_type = "debit"
    credit_type = "credit"
    both_types = "debit and credit"


class User(db.Model, ModelViewsMix):
    
    __tablename__ = 'User'

    id = db.Column(db.String, primary_key=True)
    user_type_id = db.Column(db.String(), db.ForeignKey('UserType.id'))
    firstname = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    image_url = db.Column(db.String)
    authorization_code = db.Column(db.String, unique=True)
    authorization_code_status = db.Column(db.Boolean, default=False)
    wallet = db.relationship('Wallet', cascade="all,delete-orphan", backref='user_wallet', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<User %r %r>' % (self.firstname, self.lastname)

    @classmethod
    def is_user_data_taken(cls, email):
       return db.session.query(db.exists().where(User.email==email)).scalar()


class UserType(db.Model, ModelViewsMix):
  
    __tablename__ = 'UserType'

    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, unique=True)
    description = db.Column(db.String, nullable=True)
    users = db.relationship('User', cascade="all,delete-orphan", backref='user_type', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow,
            onupdate=datetime.utcnow)

    def __repr__(self):
        return '<UserType %r>' % (self.title)


class PercentagePrice(db.Model, ModelViewsMix):
    
    __tablename__ = "PercentagePrice"

    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, unique=True)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow,
            onupdate=datetime.utcnow)

    def __repr__(self):
        return '<PercentagePrice %r %r>' % (self.description, self.price)


class Wallet(db.Model, ModelViewsMix):
    
    __tablename__ = 'Wallet'

    id = db.Column(db.String, primary_key=True)
    wallet_amount =  db.Column(db.Float, default=0.00)
    user_id = db.Column(db.String(), db.ForeignKey('User.id'))
    description = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<Wallet %r %r>' % (self.user_id, self.wallet_amount)


class Transaction(db.Model, ModelViewsMix):
    
    __tablename__ = 'Transaction'

    id = db.Column(db.String, primary_key=True)
    transaction_detail = db.Column(db.String, nullable=False)
    type_of_operation = db.Column(db.Enum(OperationType), nullable=False)
    type_of_transaction = db.Column(db.Enum(TransactionType), nullable=False)
    cost_of_transaction = db.Column(db.Float, default=0.00)
    receiver_amount_before_transaction = db.Column(db.Float, default=0.00)
    receiver_amount_after_transaction = db.Column(db.Float, default=0.00)
    sender_amount_before_transaction = db.Column(db.Float, default=0.00)
    sender_amount_after_transaction = db.Column(db.Float, default=0.00)
    paystack_deduction = db.Column(db.Float, default=0.00)
    receiver_id = db.Column(db.String(), db.ForeignKey('User.id'))
    sender_id = db.Column(db.String(), db.ForeignKey('User.id'))
    receiver = relationship("User", cascade="all,delete-orphan", single_parent=True, foreign_keys=[receiver_id])
    sender = relationship("User", cascade="all,delete-orphan", single_parent=True, foreign_keys=[sender_id])
    receiver_wallet_id = db.Column(db.String(), db.ForeignKey('Wallet.id'))
    sender_wallet_id = db.Column(db.String(), db.ForeignKey('Wallet.id'))
    receiver_wallet = relationship("Wallet", cascade="all,delete-orphan", single_parent=True, foreign_keys=[receiver_wallet_id])
    sender_wallet = relationship("Wallet", cascade="all,delete-orphan", single_parent=True, foreign_keys=[sender_wallet_id])
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<Transaction %r %r>' % (self.receiver_id, self.transaction_detail)


class Notification(db.Model, ModelViewsMix):
    
    __tablename__ = 'Notification'

    id = db.Column(db.String, primary_key=True)
    message = db.Column(db.String)
    recipient_id = db.Column(db.String(), db.ForeignKey('User.id'))
    sender_id = db.Column(db.String(), db.ForeignKey('User.id'))
    recipient = relationship("User", cascade="all,delete-orphan", single_parent=True, foreign_keys=[recipient_id])
    sender = relationship("User", cascade="all,delete-orphan", single_parent=True, foreign_keys=[sender_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<Transaction %r %r>' % (self.message)


def fancy_id_generator(mapper, connection, target):
    '''
    A function to generate unique identifiers on insert
    '''
    push_id = PushID()
    target.id = push_id.next_id()

# associate the listener function with models, to execute during the
# "before_insert" event
tables = [User, UserType, Wallet, Transaction, Notification, PercentagePrice]

for table in tables:
    event.listen(table, 'before_insert', fancy_id_generator)
