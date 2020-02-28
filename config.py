import os
from tempfile import mkdtemp
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # Database configuration
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'finance_db.db')
    SQLALCHEMY_DATABASE_URI = "postgres://zobaewcbuyscho:5925d9a5e48f113b77a6541f2ef92dfd2e8007cadc10e1bd3bbe603ddd3e5173@ec2-54-80-184-43.compute-1.amazonaws.com:5432/deaa39vqop4tsb"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Ensure templates are auto-reloaded
    TEMPLATES_AUTO_RELOAD = True

    # Configure session to use filesystem (instead of signed cookies)
    #SESSION_FILE_DIR = mkdtemp()
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"