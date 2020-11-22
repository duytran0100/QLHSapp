from flask import Flask
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:12345678@localhost/qlhsdb?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key="!@@#@!#%$^$%^@!#!@#"

db = SQLAlchemy(app=app)
admin = Admin(app=app,name="Quản lí học sinh", template_mode="Bootstrap4")
login = LoginManager(app=app)