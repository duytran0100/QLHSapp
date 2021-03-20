from QLHS.models import *
from QLHS import db, app
from datetime import date
from sqlalchemy import func
import os
import csv


def add_student(name, gender, day_of_birth, address,email):
    student = Student(name=name, gender=gender, day_of_birth=day_of_birth, address=address, email=email)

    try:
        db.session.add(student)
        db.session.commit()
        return True
    except:
        return False


def add_student_attendance(student_id, class_id):
    student = Student.query.get(student_id)
    student.class_id = class_id
    try:
        db.session.commit()
        return True
    except:
        return False


def get_class_list(class_id):
    students = Student.query.join(Class, Student.class_id == Class.id).filter(Class.id == class_id)

    return students


def search_student(student_name, class_id, school_year):
    students = Student.query
    avg_score={}
    hk1 = None
    hk2 = None
    if student_name:
        students = students.filter(Student.name.contains(student_name))
    if class_id:
        students = students.join(Class, Student.class_id == Class.id).filter(Class.id == class_id)
    if school_year:
        semesters = Semester.query.filter(Semester.school_year == school_year)
        for student in students:
            for semester in semesters:
                if semester.name == "Học kỳ 1":
                    hk1 = student_avg_score(student.id, semester.id)
                else:
                    hk2 = student_avg_score(student.id, semester.id)
            avg_score[student.id] = {'hk1': hk1, 'hk2': hk2}

    return students.all(),avg_score


def report(semester_id, subject_id=None):
    classes = Class.query.all()
    pass_score = Regulation.query.get(4).value
    report_info ={
        "semester": "{} ({})".format(Semester.query.get(semester_id).name, Semester.query.get(semester_id).school_year),
        "subject": Subject.query.get(subject_id).name if subject_id else None
    }
    report_result = {}
    for c in classes:
        students = Student.query.filter(Student.class_id == c.id)
        count_student_pass = 0
        for student in students:
            avg_score = student_avg_score(student_id=student.id, semester_id=semester_id, subject_id=subject_id)
            if avg_score[0][0] != None and avg_score[0][0] >= pass_score:
                count_student_pass += 1
        report_result[c.id] = {
            "class_id": c.id,
            "class_name": c.name,
            "num_of_student": students.count(),
            "num_of_pass_student": count_student_pass
        }

    return report_info, report_result


def student_avg_score(student_id, semester_id, subject_id=None):
    result = db.session.query(func.avg(ScoreDetail.score).label('Diem_TB')).\
            join(Score, Score.id == ScoreDetail.score_id)
    result = result.filter(Score.student_id == student_id, Score.semester_id == semester_id)

    if subject_id:
        result = result.filter(Score.subject_id == subject_id)

    return result.all()


def get_age_of_student(day_of_birth):
    day_of_birth = str(day_of_birth).split('-')
    age = date.today().year-int(day_of_birth[0])
    return age


def is_division_exist(class_id, subject_id, semester_id, teacher_id):
    division = Teach.query.filter(Teach.class_id == class_id, Teach.subject_id == subject_id,
                                  Teach.semester_id == semester_id, Teach.teacher_id == teacher_id).first()

    return division


def create_division(class_id, subject_id, semester_id, teacher_id):
    division = Teach(class_id=class_id, subject_id=subject_id, semester_id=semester_id,
                     teacher_id=teacher_id)
    try:
        db.session.add(division)
        db.session.commit()
        return True
    except:
        return False


def get_division_list():
    division_list = db.session.query(Teach.id, Class.name, Subject.name,
                                     Semester.name, Semester.school_year, Teacher.name).\
        join(Teach, Teach.class_id == Class.id).join(Subject, Subject.id == Teach.subject_id).\
        join(Semester, Semester.id == Teach.semester_id).\
        join(Teacher, Teacher.id == Teach.teacher_id).all()

    return division_list


def search_teacher(teacher_name, major_name):
    teachers = Teacher.query

    if teacher_name:
        teachers = teachers.filter(Teacher.name.contains(teacher_name))
    if major_name:
        teachers = teachers.filter(Teacher.major == major_name)

    return teachers.all()


def get_subject_score(class_id, subject_id, semester_id):
    score_list = {}
    class_name = Class.query.get(class_id).name
    subject = Subject.query.get(subject_id)
    semester = Semester.query.get(semester_id)
    info = {
        "class": class_name,
        "subject": subject.name,
        "semester": "{} ({})".format(semester.name, semester.school_year)
    }
    students = db.session.query(Student.id).filter(Student.class_id == class_id).all()
    for student in students:
        score_list[student[0]] = get_student_score(student_id=student[0],
                                                   subject_id=subject_id, semester_id=semester_id)

    return score_list, info


def get_student_score(student_id, subject_id, semester_id):
    score_15 = []
    score_45 = []
    score_hk = []
    student = Student.query.get(student_id)
    p = db.session.query(ScoreDetail.score_type, ScoreDetail.score, Student.name).\
        join(Score, Student.id == Score.student_id, isouter=True).\
        join(ScoreDetail, Score.id == ScoreDetail.score_id, isouter=True).\
        filter(Student.id == student_id,
               Score.subject_id == subject_id, Score.semester_id == semester_id).all()
    for s in p:
        if s[0] == "15 phút":
            score_15.append(s[1])
        if s[0] == "1 tiết":
            score_45.append(s[1])
        if s[0] == "Học kỳ":
            score_hk.append(s[1])

    scores = {
        "id": student.id,
        "name": student.name,
        "15": score_15,
        "45": score_45,
        "hk": score_hk
    }

    return scores


def create_score_record(student_id, semester_id, subject_id):
    score = Score(student_id=student_id, semester_id=semester_id, subject_id=subject_id)
    try:
        db.session.add(score)
        db.session.commit()
        return True
    except:
        return False


def add_score(student_id, semester_id, subject_id, score, score_type):
    p = Score.query.filter(Score.student_id == student_id, Score.semester_id == semester_id,
                           Score.subject_id == subject_id).first()
    score_detail = ScoreDetail(score_id=p.id, score=score, score_type=score_type)
    try:
        db.session.add(score_detail)
        db.session.commit()
        return True
    except:
        return False
