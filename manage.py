import os

from flask_script import Manager, Server
from flask_migrate import MigrateCommand

from main import create_flask_app


environment = os.getenv("FLASK_CONFIG")
app = create_flask_app(environment)

app.secret_key = os.getenv("APP_SECRET")

port = int(os.environ.get('PORT', 5000))
server = Server(host="0.0.0.0", port=port)

# initialize flask script
manager = Manager(app)

# enable migration commands
manager.add_command("runserver", server)
manager.add_command("db", MigrateCommand)

@manager.command
def seed_default_data(prompt=True):
    pass

manager.run()
