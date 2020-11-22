from flask import render_template,redirect,request,url_for
from QLHS import app,login
from QLHS.models import *
from flask_login import login_user
import hashlib


@app.route('/')
def index():

    return render_template("index.html")


@app.route('/login-admin',methods=['get', 'post'])
def login_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password',"")
        password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
        user = User.query.filter(User.username == username,User.password == password,
                                 User.user_role == UserRole.ADMIN).first()
        if user:
            login_user(user=user)
    return redirect("/admin")


@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)


if __name__ == "__main__":
    app.run(debug=True)