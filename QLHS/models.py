from sqlalchemy import Integer, Float, String, Column, ForeignKey, Boolean,Enum,Date
from sqlalchemy.orm import relationship
from QLHS import db,admin
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask import redirect
from flask_login import UserMixin,current_user,logout_user
from datetime import datetime
from enum import Enum as UserEnum


class Base(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)

    def __str__(self):
        return self.name


class UserRole(UserEnum):
    USER = 1
    ADMIN = 2


class User(Base,UserMixin):
    username = Column(String(50),nullable=False,unique=True)
    password = Column(String(50),nullable=False)
    active = Column(Boolean, default=True)
    joined_date = Column(Date,default=datetime.now())
    user_role = Column(Enum(UserRole), default=UserRole.USER)


class Teacher(Base):
    address = Column(String(100))
    email = Column(String(50),nullable=False)


class Class(Base):
    class_size = Column(Integer,default=40)


class Subject(Base):
    pass


# View
class LogoutView(BaseView):
    @expose('/')
    def __index__(self):
        logout_user()

        return redirect("/admin")

    def is_accessible(self):
        return current_user.is_authenticated

class AboutUsView(BaseView):
    @expose('/')
    def __index__(self):
        return self.render("admin/about-us.html")

class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated


admin.add_view(AuthenticatedView(Teacher,db.session,name="Giáo Viên"))
admin.add_view(AuthenticatedView(Class,db.session,name="Lớp học"))
admin.add_view(AuthenticatedView(Subject,db.session,name="Môn học"))
admin.add_view(AuthenticatedView(User,db.session,name="Tài khoản"))
admin.add_view(AboutUsView(name="About Us"))
admin.add_view(LogoutView(name="Đăng Xuất"))


if __name__ == "__main__":
    db.create_all()
    # password : 123456
    # admin = User(name = "admin", username="admin",password ="e10adc3949ba59abbe56e057f20f883e",
    #              active =1,user_role=UserRole.ADMIN)
    # db.session.add(admin)
    # db.session.commit()
