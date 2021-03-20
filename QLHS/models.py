from sqlalchemy import Column, Integer, Float, String, \
    Boolean, Enum, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship, backref
from QLHS import db, admin
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin, current_user, logout_user
from enum import Enum as UserEnum
from datetime import datetime
from flask import redirect, request
import hashlib


class Base(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)

    def __str__(self):
        return self.name


class UserRole(UserEnum):
    USER = 1
    ADMIN = 2
    MANAGE = 3


class User(db.Model, UserMixin):

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    active = Column(Boolean, default=True)
    joined_date = Column(DateTime, default=datetime.now)
    user_role = Column(Enum(UserRole), default=UserRole.USER)
    teacher = relationship('Teacher', backref='user', uselist=False)

    def __str__(self):
        return self.username


class Teacher(Base):

    email = Column(String(50), nullable=False, unique=True)
    address = Column(String(100))
    major = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    teach = relationship('Teach', backref='teacher', lazy=True)


class Grade(Base):

    classes = relationship('Class', backref='grade', lazy=True)


class Class(Base):
    grade_id = Column(Integer, ForeignKey(Grade.id), nullable=False)
    students = relationship('Student', backref='class', lazy=True)
    teach = relationship('Teach', backref='class', lazy=True)


subject_semester = db.Table('subject_semester',
                            Column('semester_id', Integer, ForeignKey('semester.id'), primary_key=True),
                            Column('subject_id', Integer, ForeignKey('subject.id'), primary_key=True),
                            extend_existing=True)


class Subject(Base):
    semesters = relationship('Semester', secondary='subject_semester', lazy='subquery',
                             backref=backref('subjects', lazy=True))
    scores = relationship('Score', backref='subject', lazy=True)
    teach = relationship('Teach', backref='subject', lazy=True)


class Student(Base):
    gender = Column(Integer, nullable=False)
    day_of_birth = Column(Date, nullable=False)
    address = Column(String(100))
    email = Column(String(50), nullable=True, unique=True)
    class_id = Column(Integer, ForeignKey(Class.id))
    scores = relationship('Score', backref='student', lazy=True)


class Semester(Base):
    school_year = Column(String(50), nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    scores = relationship('Score', backref='semester', lazy=True)
    teach = relationship('Teach', backref='semester', lazy=True)


class Score(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey(Student.id), nullable=False)
    subject_id = Column(Integer, ForeignKey(Subject.id), nullable=False)
    semester_id = Column(Integer, ForeignKey(Semester.id), nullable=False)
    score_detail = relationship('ScoreDetail', backref='Score', lazy=True)


class ScoreDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    score_id = Column(Integer, ForeignKey(Score.id), nullable=False)
    score = Column(Float, nullable=False)
    score_type = Column(String(50), nullable=False)


class Teach(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey(Class.id), nullable=False)
    subject_id = Column(Integer, ForeignKey(Subject.id), nullable=False)
    teacher_id = Column(Integer, ForeignKey(Teacher.id), nullable=False)
    semester_id = Column(Integer, ForeignKey(Semester.id), nullable=False)


class Regulation(Base):
    value = Column(Integer, nullable=False)
    description = Column(String(100), nullable=False)


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


class ResetPasswordView(BaseView):
    @expose('/', methods=('GET', 'POST'))
    def __index__(self):
        err_msg = ""
        if request.method == 'POST':
            if request.method == 'POST':
                username = request.form.get('username')
                user = User.query.filter(User.username == username).first()
                if user:
                    password = request.form.get('password')
                    confirm_password = request.form.get('confirm-password')
                    if password == confirm_password:
                        user.password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
                        db.session.commit()
                        err_msg = "Thay đổi mật khẩu thành công"
                    else:
                        err_msg = "Mật khẩu xác nhận không khớp"
                else:
                    err_msg = "Tài khoản không tồn tại"
        return self.render("admin/reset-password.html", err_msg=err_msg)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class CreateAccountView(BaseView):
    @expose('/', methods=('GET', 'POST'))
    def __index__(self):
        err_msg = ""
        if request.method == 'POST':
            username = request.form.get('username')
            user = User.query.filter(User.username == username).first()
            if user:
                err_msg = "Tên tài khoản đã tồn tại"
            else:
                password = request.form.get('password')
                confirm_password = request.form.get('confirm-password')
                if password == confirm_password:
                    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
                    user = User(username=username, password=password)
                    db.session.add(user)
                    db.session.commit()
                    err_msg = "Tạo tài khoản thành công"
                else:
                    err_msg = "Mật khẩu không khớp"

        return self.render('admin/create-account.html',err_msg=err_msg)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class AuthenticatedView(ModelView):
    column_display_pk = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class UserView(AuthenticatedView):
    can_create = False
    can_edit = True
    can_delete = True


class ScoreView(AuthenticatedView):
    column_list = (ScoreDetail.score_id, ScoreDetail.score, ScoreDetail.score_type)


class RegulationsView(AuthenticatedView):
    can_create = False
    can_delete = False
    can_edit = True


admin.add_view(UserView(User, db.session, name="Tài khoản", category="Quản lý GV"))
admin.add_view(AuthenticatedView(Teacher, db.session, name="Giáo viên", category="Quản lý GV"))
admin.add_view(UserView(Teach, db.session, name="Phân công", category="Quản lý GV"))
admin.add_view(AuthenticatedView(Student, db.session, name="Học sinh"))
admin.add_view(AuthenticatedView(Grade, db.session, name="Khối học", category="Lớp"))
admin.add_view(AuthenticatedView(Class, db.session, name="Lớp học", category="Lớp"))
admin.add_view(AuthenticatedView(Subject, db.session, name="Môn học", category="Học"))
admin.add_view(AuthenticatedView(Semester, db.session, name='Học kỳ', category="Học"))
admin.add_view(AuthenticatedView(Score, db.session, name='Điểm', category='Quản lý điểm'))
admin.add_view(ScoreView(ScoreDetail, db.session, name='Chi tiết điểm', category='Quản lý điểm'))
admin.add_view(RegulationsView(Regulation, db.session, name='Qui định'))
admin.add_view(ResetPasswordView(name="Reset password", category="Chức năng"))
admin.add_view(CreateAccountView(name="Tạo tài khoản", category="Chức năng"))
admin.add_view(AboutUsView(name="About us"))
admin.add_view(LogoutView(name="Đăng xuất"))


if __name__ == '__main__':
    db.create_all()
