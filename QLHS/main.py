from flask import render_template, redirect, request, url_for, send_file
from QLHS import app, login, db
from QLHS.models import Class, Student, Teacher, User, UserRole, Score, Subject, Semester,Regulation
from flask_login import login_user, logout_user, current_user
import hashlib
from QLHS import utils, decorator
from sqlalchemy import or_


@app.route('/')
def index():
    total_student = Student.query.count()
    total_teacher = Teacher.query.count()
    total_class = Class.query.count()
    total_subject = Subject.query.count()
    teacher = ""
    user_role = UserRole
    if current_user.is_authenticated:
        teacher = Teacher.query.filter(Teacher.user_id == current_user.id).first()
    return render_template("index.html", total_student=total_student,
                           total_teacher=total_teacher, total_class=total_class,
                           total_subject=total_subject, teacher=teacher, user_role=user_role)


@app.route('/login', methods=['get', 'post'])
def login_usr():
    errmsg = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password', '')
        password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
        user = User.query.filter(User.username == username, User.password == password).first()
        if user:
            login_user(user=user)

            if 'next' in request.args:
                return redirect(request.args['next'])

            return redirect(url_for('index'))
        else:
            errmsg = 'Sai tài khoản hoặc mật khẩu'

    return render_template('login.html', errmsg=errmsg)


@app.route('/logout')
def logout_usr():
    logout_user()

    return redirect(url_for('index'))


@app.route('/change-password', methods=['get', 'post'])
@decorator.login_required
def change_password():
    errmsg = ''
    if request.method == 'POST':
        old_password = request.form.get('old-password', '')
        new_password = request.form.get('new-password', '')
        confirm_password = request.form.get('confirm-password', '')
        old_password = str(hashlib.md5(old_password.encode('utf-8')).hexdigest())
        password = current_user.password
        if old_password == password:
            if confirm_password == new_password:
                user = User.query.get(current_user.id)
                user.password = str(hashlib.md5(new_password.encode('utf-8')).hexdigest())
                db.session.commit()

                return redirect(url_for('logout_usr'))
            else:
                errmsg = 'Mật khẩu xác nhận không khớp'
        else:
            errmsg = 'Sai mật khẩu cũ'

    return render_template('change-password.html', errmsg=errmsg)


# student
@app.route('/student')
@decorator.login_required
def student():
    student_list = Student.query.filter()
    user_role = UserRole

    return render_template('student.html', student_list=student_list, user_role=user_role)


@app.route('/student/add', methods=['get', 'post'])
@decorator.login_required
@decorator.manage_permission_required
def add_student():
    user_role = UserRole
    errmsg = ''
    min_age = Regulation.query.get(2).value
    max_age = Regulation.query.get(1).value
    if request.method == 'POST':
        name = request.form.get('name')
        gender = request.form.get('gender')
        day_of_birth = request.form.get('day-of-birth')
        address = request.form.get('address')
        email = request.form.get('email')
        age = utils.get_age_of_student(day_of_birth)
        if min_age <= age <= max_age:
            if Student.query.filter(Student.email == email).first():
                errmsg = 'Email đã tồn tại'
            else:
                utils.add_student(name=name, gender=gender, day_of_birth=day_of_birth,
                                  address=address, email=email)
                return redirect(url_for('student'))
        else:
            errmsg = 'Tuổi không hợp lệ'

    return render_template('add-student.html', errmsg=errmsg, user_role=user_role)


@app.route('/student-lookup', methods=['get', 'post'])
@decorator.login_required
def student_lookup():
    user_role = UserRole
    classes = Class.query.filter().all()
    school_years = db.session.query(Semester.school_year).filter().group_by(Semester.school_year)
    student_name = request.args.get("student-name", "")
    class_id = request.args.get("class-id", "")
    school_year = request.args.get("school-year")
    students = ""
    avg_score = ""
    if student_name or class_id:
        students, avg_score = utils.search_student(student_name=student_name,
                                        class_id=class_id, school_year=school_year)

    return render_template('student-lookup.html', classes=classes,avg_score=avg_score,
                           students=students, school_years=school_years, user_role=user_role)


# teacher
@app.route('/teacher')
@decorator.login_required
def teacher():
    teacher_list = Teacher.query.filter()
    user_role = UserRole

    return render_template('teacher.html', teacher_list=teacher_list,user_role=user_role)


@app.route('/teacher/teach', methods=['post', 'get'])
@decorator.login_required
@decorator.manage_permission_required
def teach():
    user_role = UserRole
    classes = Class.query.all()
    teachers = Teacher.query.all()
    subjects = Subject.query.all()
    semesters = Semester.query.all()
    division_list = utils.get_division_list()
    errmsg = ''
    if request.method == 'POST':
        class_id = request.form.get('class-id')
        subject_id = request.form.get('subject-id')
        semester_id = request.form.get('semester-id')
        teacher_id = request.form.get('teacher-id')
        if utils.is_division_exist(class_id=class_id, semester_id=semester_id,
                                   subject_id=subject_id, teacher_id=teacher_id):
            errmsg = "Lịch phân công đã tồn tại"
        else:
            utils.create_division(class_id=class_id, semester_id=semester_id,
                                  subject_id=subject_id, teacher_id=teacher_id)
            division_list = utils.get_division_list()

    return render_template('teach.html', classes=classes, teachers=teachers,
                           subjects=subjects, semesters=semesters,
                           division_list=division_list, errmsg=errmsg, user_role=user_role)


@app.route('/teacher-lookup', methods=['get'])
def teacher_lookup():
    user_role = UserRole
    subjects = Subject.query.all()
    teacher_name = request.args.get('teacher-name', "")
    major_name = request.args.get('major-name', "")
    teachers = ""
    if teacher_name or major_name:
        teachers = utils.search_teacher(teacher_name=teacher_name, major_name=major_name)

    return render_template('teacher-lookup.html', subjects=subjects,
                           teachers=teachers, user_role=user_role)


# class
@app.route('/class', methods=['get', 'post'])
@decorator.login_required
def class_page():
    user_role = UserRole
    classes = Class.query.filter()
    class_id = request.args.get("class-id")
    class_name = Class.query.get(class_id)
    students = utils.get_class_list(class_id)
    num_of_pupils = students.count()

    return render_template('class.html', classes=classes, class_name=class_name,
                           students=students, num_of_pupils=num_of_pupils, user_role=user_role)


@app.route('/class/class-attendance', methods=['post', 'get'])
@decorator.login_required
@decorator.manage_permission_required
def class_attendance():
    user_role = UserRole
    classes = Class.query.filter()
    class_id = request.args.get("class-id")
    class_name = Class.query.get(class_id)
    num_of_pupils = utils.get_class_list(class_id).count()
    max_num_of_pupils = Regulation.query.get(3).value
    students = Student.query.filter(or_(Student.class_id != class_id, Student.class_id == None))
    errmsg = ""
    if request.method == "POST":
        students_id = request.form.getlist('student-id')
        if num_of_pupils + len(students_id) <= max_num_of_pupils:
            for id in students_id:
                utils.add_student_attendance(student_id=id, class_id=class_id)
            return redirect(url_for('class_page'))
        else:
            errmsg = "Vượt quá sĩ số tối đa"

    return render_template('class-attendance.html', classes=classes, class_name=class_name,
                           class_id=class_id, num_of_pupils=num_of_pupils, students=students,
                           errmsg=errmsg, user_role=user_role)


# subject
@app.route('/subject')
@decorator.login_required
def subject():
    user_role = UserRole
    subjects = Subject.query.all()

    return render_template('subject.html', subjects=subjects, user_role=user_role)


# score
@app.route('/score', methods=['post', 'get'])
@decorator.login_required
def score():
    user_role = UserRole
    classes = Class.query.all()
    subjects = Subject.query.all()
    semesters = Semester.query.all()
    score_list = {}
    class_id = 0
    subject_id = 0
    semester_id = 0
    info = ""  # Thông tin về lớp học, học kỳ, môn học
    if request.method == 'POST':
        class_id = request.form.get('class-id')
        subject_id = request.form.get('subject-id')
        semester_id = request.form.get('semester-id')
        score_list, info = utils.get_subject_score(class_id=class_id,
                                                   subject_id=subject_id, semester_id=semester_id)

    return render_template('score.html', classes=classes, subjects=subjects,
                           class_id=class_id, subject_id=subject_id, semester_id=semester_id,
                           semesters=semesters, score_list=score_list, info=info, user_role=user_role)


@app.route('/score/add/<int:student_id>/<int:class_id>/<int:semester_id>/<int:subject_id>', methods=['post', 'get'])
def add_score(student_id, class_id, semester_id, subject_id):
    user_role = UserRole
    student_name = Student.query.get(student_id).name
    class_name = Class.query.get(class_id).name
    semester = Semester.query.get(semester_id)
    subject_name = Subject.query.get(subject_id).name
    errmsg = ""
    if not Score.query.filter(Score.student_id == student_id, Score.semester_id == semester_id,
                              Score.subject_id == subject_id).first():
        utils.create_score_record(student_id=student_id, subject_id=subject_id, semester_id=semester_id)

    if request.method == 'POST':
        score = request.form.get('score')
        score_type = request.form.get('score-type')
        if 0 <= float(score) <= 10:
            utils.add_score(student_id=student_id, semester_id=semester_id,
                            subject_id=subject_id, score=score, score_type=score_type)
            errmsg = "Thêm điểm thành công"
        else:
            errmsg = "Điểm không hợp lệ"

    return render_template('add-score.html', student_name=student_name, class_name=class_name,
                           semester=semester, subject_name=subject_name, errmsg=errmsg, user_role=user_role)


# report
@app.route('/subject-report', methods=['get'])
@decorator.login_required
@decorator.manage_permission_required
def subject_report():
    user_role = UserRole
    semesters = Semester.query.all()
    subjects = Subject.query.all()
    semester_id = request.args.get('semester-id', "")
    subject_id = request.args.get('subject-id', "")
    report_info, report = {}, {}
    if semester_id and subject_id:
        report_info, report = utils.report(semester_id=semester_id, subject_id=subject_id)

    return render_template('subject-report.html', semesters=semesters, subjects=subjects,
                           report=report, report_info=report_info, user_role=user_role)


@app.route('/semester-report', methods=['get'])
@decorator.login_required
@decorator.manage_permission_required
def semester_report():
    user_role = UserRole
    semesters = Semester.query.all()
    semester_id = request.args.get('semester-id', "")
    report_info, report = {}, {}
    if semester_id:
        report_info, report = utils.report(semester_id=semester_id)

    return render_template('semester-report.html', semesters=semesters,
                           report_info=report_info, report=report, user_role=user_role)


# admin

@app.route('/login-admin', methods=['get', 'post'])
def login_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password', "")
        password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
        user = User.query.filter(User.username == username, User.password == password,
                                 User.user_role == UserRole.ADMIN).first()
        if user:
            login_user(user=user)
    return redirect("/admin")


@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)



if __name__ == "__main__":
    app.run(debug=True)
