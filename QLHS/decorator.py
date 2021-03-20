from functools import wraps
from flask_login import current_user
from flask import redirect, url_for, request
from QLHS.models import UserRole


def login_required(f):
    @wraps(f)
    def check(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_usr', next=request.url))
        return f(*args, **kwargs)
    return check


def manage_permission_required(f):
    @wraps(f)
    def check(*args, **kwargs):
        if current_user.user_role == UserRole.USER:
            return redirect(url_for('login_usr', next=request.url))
        return f(*args, **kwargs)
    return check
