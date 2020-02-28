import os
from flask import Flask
from config import Config
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
Session(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Make sure API key is set
if not os.environ.get("API_KEY"):
    try:
        os.environ["API_KEY"]="pk_9efea07c93fd4fefa2fd735c8ee0c40c"
    except:
        raise RuntimeError("API_KEY not set")

from app import routes, models