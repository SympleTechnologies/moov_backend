import os

from flask_script import Manager, Server, prompt_bool, Shell
from flask_migrate import MigrateCommand
from sqlalchemy.exc import SQLAlchemyError

from main import create_flask_app

try:
    from api.helper.default_data import (
        create_default_user, create_default_user_types
    )
    from api.models import db, UserType
except ImportError:
    from moov_backend.api.helper.default_data import (
        create_default_user, create_default_user_types
    )
    from moov_backend.api.models import db, UserType


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
        print("\n\n\tNot happening! Aborting...\n\n")
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
                print("\n\n\tCommand could not execute due to the error below! Aborting...\n\n\n" + str(error) + "\n\n")
                return

            try:
                # seed default user_types
                create_default_user_types()

                # seed default user
                user_type_id = UserType.query.filter_by(title="admin").first().id
                create_default_user(user_type_id)

                message = "\n\n\tYay *\(^o^)/* \n\n Your database has been succesfully seeded !!! \n\n\t *\(@^_^@)/* <3 <3 \n\n"
            except SQLAlchemyError as error:
                db.session.rollback()
                message = "\n\n\tThe error below occured when trying to seed the database\n\n\n" + str(error) + "\n\n"

            print(message)

        else:
            print("\n\n\tAborting...\n\n")

    else:
        print("\n\n\tAborting... Invalid environment '{}'.\n\n"
              .format(environment))

manager.run()
