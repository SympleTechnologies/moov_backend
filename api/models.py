# models
import os
import json
import enum

from alembic import op
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref, relationship

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.types import JSON, TEXT, TypeDecorator
from sqlalchemy import event, and_
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


# enums
class OperationType(enum.Enum):
    transfer_type = "transfer"
    wallet_type = "load_wallet"
    ride_type = "ride_fare"
    borrow_type = "borrow_me"
    cancel_type = "cancel_ride"


class TransactionType(enum.Enum):
    debit_type = "debit"
    credit_type = "credit"
    both_types = "debit and credit"


class FreeRideType(enum.Enum):
    social_share_type = "social_share"
    ride_type="ride"


class RatingsType(enum.Enum):
    no_ratings = None
    one = 1
    two = 2
    three = 3
    four = 4
    five = 5


# models
class RateMe(db.Model, ModelViewsMix):
    
    __tablename__ = 'RateMe'

    id = db.Column(db.String, primary_key=True)
    rating_type = db.Column(db.Enum(RatingsType), nullable=False)
    ratee_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    rater_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    ratee = relationship("User", single_parent=True, foreign_keys=[ratee_id])
    rater = relationship("User", single_parent=True, foreign_keys=[rater_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 

    def __repr__(self):
        return '<RateMe ratee-%r rater-%r>' % (self.ratee_id, self.rater_id) 


class User(db.Model, ModelViewsMix):
    
    __tablename__ = 'User'

    id = db.Column(db.String, primary_key=True)
    user_type_id = db.Column(db.String(), db.ForeignKey('UserType.id', ondelete='SET NULL'))
    user_id = db.Column(db.String, unique=True)
    firstname = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    image_url = db.Column(db.String)
    mobile_number = db.Column(db.String, nullable=False)
    authorization_code = db.Column(db.String, unique=True)
    authorization_code_status = db.Column(db.Boolean, default=False)
    number_of_rides = db.Column(db.Integer, default=0)
    ratings = db.Column(db.Integer, nullable=True)
    wallet_user = db.relationship('Wallet', cascade="all,delete-orphan", back_populates='user_wallet')
    free_ride = db.relationship('FreeRide', backref='user_free_ride', lazy='dynamic')
    driver_info = db.relationship('DriverInfo', cascade="all,delete-orphan", backref='driver_information', lazy='dynamic')
    school_info = db.relationship('SchoolInfo', cascade="all,delete-orphan", backref='school_information', lazy='dynamic')
    admission_type = db.relationship('AdmissionType', backref='school_admission_type', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<User %r %r>' % (self.firstname, self.lastname)

    @classmethod
    def is_user_data_taken(cls, email):
       return db.session.query(db.exists().where(User.email==email)).scalar()

    @classmethod
    def get_average_ratings(cls):
        total_ratings = 0
        my_ratings = RateMe.query.filter(and_(
                        RateMe.ratee_id==User.id,
                        RateMe.rating!="RatingsType.no_ratings"
                    )).all()

        my_ratings_count = len(my_ratings)
        if my_ratings_count == 0:
            return None

        for rating in my_ratings:
            if rating.rating_type == "RatingsType.one":
                total_ratings += 1
            if rating.rating_type == "RatingsType.two":
                total_ratings += 2
            if rating.rating_type == "RatingsType.three":
                total_ratings += 3
            if rating.rating_type == "RatingsType.four":
                total_ratings += 4
            if rating.rating_type == "RatingsType.five":
                total_ratings += 5

        average_ratings = int(round(total_ratings / my_ratings_count, 0))
        return average_ratings 


class UserType(db.Model, ModelViewsMix):
  
    __tablename__ = 'UserType'

    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, unique=True)
    description = db.Column(db.String, nullable=True)
    users = db.relationship('User', backref='user_type', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow,
            onupdate=datetime.utcnow)

    def __repr__(self):
        return '<UserType %r>' % (self.title)


class FreeRide(db.Model, ModelViewsMix):
    
    __tablename__ = 'FreeRide'

    id = db.Column(db.String, primary_key=True)
    free_ride_type = db.Column(db.Enum(FreeRideType), nullable=False)
    token = db.Column(db.String, unique=True, nullable=False)
    token_status = db.Column(db.Boolean, default=False)
    description = db.Column(db.String, nullable=True)
    user_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<FreeRide %r>' % (self.user_id)


class DriverInfo(db.Model, ModelViewsMix):
    
    __tablename__ = 'DriverInfo'

    id = db.Column(db.String, primary_key=True)
    location_latitude = db.Column(db.Float, nullable=True)
    location_longitude = db.Column(db.Float, nullable=True)
    destination_latitude = db.Column(db.Float, nullable=True)
    destination_longitude = db.Column(db.Float, nullable=True)
    car_slots = db.Column(db.Integer, nullable=False)
    available_car_slots = db.Column(db.Integer, default=0)
    status = db.Column(db.Boolean, default=False)
    on_trip_with = db.Column(json_type, nullable=True)
    car_model = db.Column(db.String)
    left_image = db.Column(db.String)
    right_image = db.Column(db.String)
    front_image = db.Column(db.String)
    back_image = db.Column(db.String)
    plate_number = db.Column(db.String)
    admin_confirmed = db.Column(db.Boolean, default=False)
    bank_name = db.Column(db.String)
    account_number = db.Column(db.String)
    driver_id = db.Column(db.String(), db.ForeignKey('User.id'), unique=True)
    admission_type_id = db.Column(db.String(), db.ForeignKey('AdmissionType.id', ondelete='SET NULL'))
    number_of_rides = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<DriverInfo %r>' % (self.driver_id)


class SchoolInfo(db.Model, ModelViewsMix):
    
    __tablename__ = "SchoolInfo"

    id = db.Column(db.String, primary_key=True)
    school_id = db.Column(db.String(), db.ForeignKey('User.id'), unique=True)
    account_number = db.Column(db.String)
    bank_name = db.Column(db.String)
    mobile_number = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<SchoolInfo %r>' % (self.school_id)


class AdmissionType(db.Model, ModelViewsMix):
    
    __tablename__ = "AdmissionType"

    id = db.Column(db.String, primary_key=True)
    admission_type = db.Column(db.String, unique=True)
    description = db.Column(db.String)
    school_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'), unique=True)
    driver_info = db.relationship('DriverInfo', backref='admission_driver_info', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<AdmissionType %r>' % (self.admission_type)


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
    user_wallet = db.relationship('User', back_populates='wallet_user')
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
    receiver_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    sender_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    receiver = relationship("User", single_parent=True, foreign_keys=[receiver_id])
    sender = relationship("User", single_parent=True, foreign_keys=[sender_id])
    receiver_wallet_id = db.Column(db.String(), db.ForeignKey('Wallet.id', ondelete='SET NULL'))
    sender_wallet_id = db.Column(db.String(), db.ForeignKey('Wallet.id', ondelete='SET NULL'))
    receiver_wallet = relationship("Wallet", single_parent=True, foreign_keys=[receiver_wallet_id])
    sender_wallet = relationship("Wallet", single_parent=True, foreign_keys=[sender_wallet_id])
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<Transaction %r %r>' % (self.receiver_id, self.transaction_detail)


class Icon(db.Model, ModelViewsMix):
    
    __tablename__ = "Icon"

    id = db.Column(db.String, primary_key=True)
    icon = db.Column(db.String, nullable=False)
    operation_type = db.Column(db.String, nullable=False, unique=True)
    notifications = db.relationship('Notification', backref='notification_icon', lazy='dynamic')

    def __repr__(self):
        return '<Icon %r>' % (self.operation_type)


class Notification(db.Model, ModelViewsMix):
    
    __tablename__ = 'Notification'

    id = db.Column(db.String, primary_key=True)
    message = db.Column(db.String)
    recipient_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    sender_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    transaction_icon_id = db.Column(db.String(), db.ForeignKey('Icon.id', ondelete='SET NULL'))
    recipient = relationship("User", single_parent=True, foreign_keys=[recipient_id])
    sender = relationship("User", single_parent=True, foreign_keys=[sender_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<Notification %r>' % (self.message)


def fancy_id_generator(mapper, connection, target):
    '''
    A function to generate unique identifiers on insert
    '''
    push_id = PushID()
    target.id = push_id.next_id()

# associate the listener function with models, to execute during the
# "before_insert" event
tables = [
            RateMe,
            User, 
            UserType, 
            Wallet, 
            Transaction, 
            Notification, 
            PercentagePrice,
            AdmissionType,
            Icon,
            SchoolInfo,
            DriverInfo,
            FreeRide
        ]

for table in tables:
    event.listen(table, 'before_insert', fancy_id_generator)
