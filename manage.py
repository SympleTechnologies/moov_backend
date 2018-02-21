import os

from flask_script import Manager, Server, prompt_bool, Shell
from flask_migrate import MigrateCommand
from sqlalchemy.exc import SQLAlchemyError

from main import create_flask_app

try:
    from api.helper.default_data import (
        create_user, create_default_user_types, create_percentage_price,
        create_wallet
    )
    from api.models import db, UserType, User, Wallet
except ImportError:
    from moov_backend.api.helper.default_data import (
        create_user, create_default_user_types, create_percentage_price,
        create_wallet
    )
    from moov_backend.api.models import db, UserType, User, Wallet


environment = os.getenv("FLASK_CONFIG")
app = create_flask_app(environment)

app.secret_key = os.getenv("APP_SECRET")

port = int(os.environ.get('PORT', 5000))
server = Server(host="0.0.0.0", port=port)

def _make_context():
    return dict(UserType=UserType)

# initialize flask script
manager = Manager(app)

# enable migration commands
manager.add_command("runserver", server)
manager.add_command("db", MigrateCommand)
manager.add_command("shell", Shell(make_context=_make_context))

@manager.command
def seed_default_data(prompt=True):
    if environment == "production":
        print("\n\n\tNot happening! Aborting...\n\n Aborted\n\n")
        return

    if environment in ["testing", "development"]:
        if (prompt_bool("\n\nAre you sure you want to seed your database, all previous data will be wiped off?")):
            try:
                # drops all the tables 
                db.drop_all()
                db.session.commit()

                # creates all the tables
                db.create_all()
            except SQLAlchemyError as error:
                db.session.rollback()
                print("\n\n\tCommand could not execute due to the error below! Aborting...\n\n Aborted\n\n" + str(error) + "\n\n")
                return

            try:
                # seed default user_types
                create_default_user_types()

                # seed default user
                admin_user_type_id = UserType.query.filter_by(title="admin").first().id
                moov_user_type_id = UserType.query.filter_by(title="moov").first().id
                school_user_type_id = UserType.query.filter_by(title="school").first().id
                car_owner_user_type_id = UserType.query.filter_by(title="car_owner").first().id

                # no wallet needed for admin
                admin_user = create_user(admin_user_type_id, "admin", os.environ.get('ADMIN_EMAIL'))
                moov = create_user(moov_user_type_id, "moov", "moov@email.com")
                school = create_user(school_user_type_id, "school", "school@email.com")
                car_owner = create_user(car_owner_user_type_id, "school", "car_owner@email.com")
                admin_user.save()

                # seed default wallets
                message = "Initial amount"
                wallet_amount = 0.0
                create_wallet(user_id=moov.id, wallet_amount=wallet_amount, message=message)
                create_wallet(user_id=school.id, wallet_amount=wallet_amount, message=message)
                create_wallet(user_id=car_owner.id, wallet_amount=wallet_amount, message=message)

                # seed percentage prices
                create_percentage_price(title="car_owner", price=0.0, description="Car owner")
                create_percentage_price(title="school", price=0.2, description="School")
                create_percentage_price(title="driver", price=0.4, description="Driver")
                create_percentage_price(title="moov", price=0.4, description="Moov")
                create_percentage_price(title="transfer", price=0.02, description="Transfer")

                message = "\n\n\tYay *\(^o^)/* \n\n Your database has been succesfully seeded !!! \n\n\t *\(@^_^@)/* <3 <3 \n\n"
            except SQLAlchemyError as error:
                db.session.rollback()
                message = "\n\n\tThe error below occured when trying to seed the database\n\n\n" + str(error) + "\n\n"

            print(message)

        else:
            print("\n\n\tAborting...\n\n\tAborted\n\n")

    else:
        print("\n\n\tAborting... Invalid environment '{}'.\n\n"
              .format(environment))

manager.run()
