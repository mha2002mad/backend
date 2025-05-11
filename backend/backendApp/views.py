import datetime
import random
from django.http import HttpResponse,HttpRequest, HttpResponseRedirect
from . import models
import json
from django.db.models import Q, Prefetch, OuterRef, Subquery
from django.db.models.functions import Cast, Concat, Coalesce
from django.db.models import fields, Value
from django import forms
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers import serialize
import uuid
from django.db import transaction



def findPresencePercentageT(course):
    up = models.attendance.objects.filter(
        ofClass__takenCourse = course,
        present = 1,
        ofStudent__stage = course.year
    ).count()
    down = models.attendance.objects.filter(
        ofClass__takenCourse = course,
        ofStudent__stage = course.year
    ).count()
    if down == 0:
        return 'NaN'
    else:
        return (up/down) * 100

def findPresencePercentageS(course, student):
    up = models.attendance.objects.filter(
        ofClass__takenCourse = course,
        present = 1,
        ofStudent = student
    ).count()
    down = models.attendance.objects.filter(
        ofClass__takenCourse = course,
        ofStudent = student
    ).count()
    if down == 0:
        return 'NaN'
    else:
        return (up/down) * 100
        

class LoginForm(forms.Form):
    class meta:
        fields = ['username', 'password', 'role']
    username = forms.CharField(
        required=True,
        max_length=100,
        min_length=8,
        widget=forms.TextInput(),
        error_messages={'required': 'Please enter your username', 'max_length': 'Username is too long', 'min_length': 'Username is too short'})
    password = forms.CharField(required=True, max_length=100, min_length=8, widget=forms.PasswordInput(), error_messages={'required': 'Please enter your password', 'max_length': 'Password is too long', 'min_length': 'Password is too short'})
    role = forms.ChoiceField(choices=[('student', 'Student'), ('teacher', 'Teacher')])

@csrf_exempt
def loadcsrf(r: HttpRequest):
    if 'csrftoken' not in r.COOKIES.values():
        resp = HttpResponse()
        resp.set_cookie('csrftoken', get_token(r))
        return resp
    return HttpResponse({})

def login(r: HttpRequest):
    user = None
    validate = LoginForm(data={
            "username": json.loads(r.body.decode('utf-8'))['username'],
            "password": json.loads(r.body.decode('utf-8'))['password'],
            "role": json.loads(r.body.decode('utf-8'))['role']
        })
    if not validate.is_valid():
        return HttpResponse(content=json.dumps(validate.errors), status=200)
    
    if json.loads(r.body.decode('utf-8'))['role'] == 'student':
        if models.studentCredentials.objects.filter(studentUserName=json.loads(r.body.decode('utf-8'))['username']).exists():
            user = models.studentCredentials.objects.filter(studentUserName=json.loads(r.body.decode('utf-8'))['username']).first()
        else:
            return HttpResponse(content=json.dumps({'message': 'invalid username'}))

        if user.studentPassword == json.loads(r.body.decode('utf-8'))['password']:
            r.session.create()
            r.session['userID'] = str(user.forStudent.studentID)
            r.session['role'] = 'S'
            r.session.save()
            return HttpResponse(content=json.dumps({'message': 'success'}))
        else:
            return HttpResponse(content=json.dumps({'message': 'invalid password'}))
    else:
        if models.tutorCredentials.objects.filter(tutorUserName=json.loads(r.body.decode('utf-8'))['username']).exists():
            user = models.tutorCredentials.objects.filter(tutorUserName=json.loads(r.body.decode('utf-8'))['username']).first()
        else:
            return HttpResponse(content=json.dumps({'message': 'invalid username'}))

        if user.tutorPassword == json.loads(r.body.decode('utf-8'))['password']:
            r.session.create()
            r.session['userID'] = str(user.forTutor.tutorID)
            r.session['role'] = 'T'
            r.session.save()
            return HttpResponse(content=json.dumps({'message': 'success'}))
        else:
            return HttpResponse(content=json.dumps({'message': 'invalid password'}))


def amILogedIn(r: HttpRequest):
    if r.session.session_key is None:
        return HttpResponse(content=json.dumps({'message': 'negative'}))
    if 'userID' not in r.session.keys():
        return HttpResponse(content=json.dumps({'message': 'negative'}))
    if 'role' not in r.session.keys():
        return HttpResponse(content=json.dumps({'message': 'negative'}))
    if r.session['role'] == 'S':
        return HttpResponse(content=json.dumps({'message': 'S'}))
    if r.session['role'] == 'T':
        return HttpResponse(content=json.dumps({'message': 'T'}))

def amIAValid(r: HttpRequest):
    if r.session.session_key is None:
         return HttpResponse(content=json.dumps({'message': 'negative'}))
    if not 'userID' in r.session.keys():
         print(r.session.get('userID'))
         return HttpResponse(content=json.dumps({'message': 'negative'}))
    if ('role' not in r.session.keys()) or r.session['role'] is not json.loads(r.body.decode('utf-8'))['role']:
         return HttpResponse(content=json.dumps({'message': 'negative'}))
    return HttpResponse(content=json.dumps({'message': 'positive'}))

def sendStudentTimeTable(r: HttpRequest):
    student = models.students.objects.filter(
        studentID = r.session['userID']
    ).first()
    data = list(models.timeTableclassDistribution.objects.filter(
        timeTableSelector__department = student.fromDepartment,
        timeTableSelector__stage = student.stage,
        course__year = student.stage
    ).annotate(
        start = Cast('sessionStart', fields.CharField()),
        end = Cast('sessionEnd', fields.CharField()),
    ).values('course__courseName', 'start', 'end', 'day'))

    return HttpResponse(json.dumps(data))

def studentLeaveRequestsHistory(r: HttpRequest):
    student = models.students.objects.filter(
        studentID = r.session['userID']
    ).first()
    data = list(models.leaveRequests.objects.filter(
      byStudent = student.studentID,
      forCourse__year = student.stage
    ).annotate(
        course = Cast('forCourse__courseName', fields.CharField())
    ).values('course', 'statusI', 'statusII'))
    
    return HttpResponse(content=json.dumps(data))

def sendWeekMonth(r: HttpRequest):
    if r.session['role'] is 'T':
        courses = list(models.courses.objects.filter(
            taughtBy__tutorID = r.session['userID']
        ))
        data = []
        for course in courses:
            val = findPresencePercentageT(course)
            data.append({'{}'.format(course.courseName): val if val != 'NaN' else 'NaN' })
        return HttpResponse(content=json.dumps(data))
    elif r.session['role'] is 'S':
        student = models.students.objects.filter(
            studentID = r.session['userID']
        ).first()
        courses = models.courses.objects.filter(
            byDepartment = student.fromDepartment,
            year = student.stage
        )
        data = []
        for course in courses:
            val = findPresencePercentageS(course, student)
            data.append({'{}'.format(course.courseName): val if val != 'NaN' else 'NaN' })
        return HttpResponse(content=json.dumps(data))


def sendTakenCoursesToStudent(r: HttpRequest):
    student = models.students.objects.filter(
        studentID = r.session['userID']
    ).first()
    courses = list(models.courses.objects.filter(
        year = student.stage,
        byDepartment = student.fromDepartment
    ).annotate(
        ID = Cast('courseID', output_field=fields.CharField())
    ).values('ID', 'courseName'))
    return HttpResponse(json.dumps(courses))


def sendTableDataToStudent(r: HttpRequest):
    student = models.students.objects.filter(
        studentID = r.session['userID']
    ).first()
    courses = models.courses.objects.filter(
        year = student.stage,
        byDepartment = student.fromDepartment
    ).annotate(
        ID = Cast('courseID', output_field=fields.CharField())
    )
    
    data = []
    for course in courses:
        data.append({
            "{}".format(course.courseName): models.attendance.objects.filter(
            ofStudent__studentID = r.session['userID'],
            ofClass__takenCourse = course,
            present = 0
        ).count()
        })
    return HttpResponse(content=json.dumps(data))


def sendStudentAttendanceStats(r: HttpRequest):
    student = models.students.objects.filter(
        studentID = r.session['userID']
    ).first()
    course = models.courses.objects.filter(courseID = json.loads(r.body.decode('utf-8'))['course']).first()
    data = list(models.attendance.objects.filter(
        ofStudent = student,
        ofClass__takenCourse__year = student.stage,
        present=0,
        ofClass__takenCourse = course
        ).annotate(
            date = Cast('ofClass__date', fields.CharField()),
        ).values('date'))
    return HttpResponse(content=json.dumps(data))

def sendAvailableCoursesToTeacher(r: HttpRequest):
    courses = models.attendance.objects.filter(
        ofClass__takenCourse__taughtBy__tutorID = r.session['userID'],
    ).distinct('ofClass__takenCourse__courseID')
    data = []
    for course in courses:
        if models.attendance.objects.filter(ofClass = course.ofClass).count() == 0:
            continue
        else:
            data.append({
                'name': course.ofClass.takenCourse.courseName,
                'ID': course.ofClass.takenCourse.courseID.__str__()
            })
    return HttpResponse(content=json.dumps(data))

def sendleaveRequestsToTeacher(r: HttpRequest):
    data = list(models.leaveRequests.objects.filter(
        forCourse__taughtBy__tutorID = r.session['userID']
    ).annotate(
        IDC = Cast('forCourse__courseID', output_field=fields.CharField()),
        course = Cast('forCourse__courseName', output_field=fields.CharField()),
        IDS = Cast('byStudent__studentID', output_field=fields.CharField()),
        student = Concat('byStudent__studentFirstName', Value(' '), 'byStudent__studentLastName'),
        date = Cast('forDate', output_field=fields.CharField())
    ).values('IDS', 'student', 'reason', 'IDC', 'course', 'date', 'statusI', 'statusII'))

    return HttpResponse(content=json.dumps(data))

def updateLeaveRequest(r: HttpRequest):
    requestData = json.loads(r.body.decode('utf-8'))
    LRI = models.leaveRequests.objects.filter(
        forCourse__courseID = requestData['course'],
        byStudent__studentID = requestData['student'],
        forDate = requestData['date']
    ).first()
    LRI.statusI = 'rejected' if requestData['status'] == 0 else 'approved'
    LRI.save()
    return HttpResponse(content=json.dumps({'message': 'positive'}))

def sendAttendance(studentName, fromDate, toDate, course):
    if studentName == '':
        data = list(
        models.attendance.objects.filter(
        ofClass__takenCourse__courseID = course,
        present = 0,
        ofClass__date__gte = fromDate,
        ofClass__date__lte = toDate,
        ).annotate(
            studentName = Concat('ofStudent__studentFirstName', Value(' '), 'ofStudent__studentLastName'),
            date = Cast('ofClass__date', output_field=fields.CharField()),
            reason = Coalesce(Subquery(
                models.leaveRequests.objects.filter(
                byStudent__studentID = OuterRef('ofStudent__studentID'),
                forCourse__courseID = course,
                forDate = OuterRef('ofClass__date'),
            ).values('reason')), Value('no reason'), output_field=fields.CharField())
        ).values(
            'studentName',
            'date',
            'reason'
        )
        )
        return data


    else:
        names = str(studentName).split(' ')
        if len(names) == 1:
            data = list(
            models.attendance.objects.filter(
            Q(ofStudent__studentFirstName__istartswith = names[0]) | Q(ofStudent__studentLastName__istartswith = names[0]),
            ofClass__takenCourse__courseID = course,
            present = 0,
            ofClass__date__gte = fromDate,
            ofClass__date__lte = toDate,
            ).annotate(
                studentName = Concat('ofStudent__studentFirstName', Value(' '), 'ofStudent__studentLastName'),
                date = Cast('ofClass__date', output_field=fields.CharField()),
                reason = Coalesce(Subquery(
                    models.leaveRequests.objects.filter(
                    byStudent__studentID = OuterRef('ofStudent__studentID'),
                    forCourse__courseID = course,
                    forDate = OuterRef('ofClass__date'),
                ).values('reason')), Value('no reason'), output_field=fields.CharField())
            ).values(
                'studentName',
                'date',
                'reason'
            )
            )
            return data
        
        else:
            data = list(
            models.attendance.objects.filter(
            Q(ofStudent__studentFirstName__istartswith = names[0]) & Q(ofStudent__studentLastName__istartswith = names[1]),
            ofClass__takenCourse__courseID = course,
            present = 0,
            ofClass__date__gte = fromDate,
            ofClass__date__lte = toDate,
            ).annotate(
                studentName = Concat('ofStudent__studentFirstName', Value(' '), 'ofStudent__studentLastName'),
                date = Cast('ofClass__date', output_field=fields.CharField()),
                reason = Coalesce(Subquery(
                    models.leaveRequests.objects.filter(
                    byStudent__studentID = OuterRef('ofStudent__studentID'),
                    forCourse__courseID = course,
                    forDate = OuterRef('ofClass__date'),
                ).values('reason')), Value('no reason'), output_field=fields.CharField())
            ).values(
                'studentName',
                'date',
                'reason'
            )
        )
    return data

def sendAttendanceRecords(r: HttpRequest):
    studentName = json.loads(r.body.decode('utf-8'))['studentName']
    fromDate = json.loads(r.body.decode('utf-8'))['fromDate']
    toDate = json.loads(r.body.decode('utf-8'))['toDate']
    course = json.loads(r.body.decode('utf-8'))['course']
    data = sendAttendance(studentName, fromDate, toDate, course)
    return HttpResponse(content=json.dumps(data))

def sendName(r: HttpRequest):
    if r.session['role'] == 'S':
        name = list(models.students.objects.filter(
            studentID = r.session['userID']
        ).annotate(
            name = Concat('studentFirstName', Value(' '), 'studentLastName')
        ).values('name'))
    else:
        name = list(models.tutors.objects.filter(
            tutorID = r.session['userID']
        ).annotate(
            name = Concat('tutorFirstName', Value(' '), 'tutorLastName')
        ).values('name'))
    return HttpResponse(content=name[0]['name'])

def sendStudentsForAttendanceInput(r: HttpRequest):
    course = json.loads(r.body.decode('utf-8'))['course']
    course = models.courses.objects.filter(courseID=course).first()

    students = list(
        models.students.objects.filter(
            stage = course.year,
            fromDepartment = course.byDepartment
        ).annotate(
            ID = Cast('studentID', output_field=fields.CharField()),
            studentName = Concat('studentFirstName', Value(' '), 'studentLastName'),
        ).values('ID', 'studentName')
    )
    return HttpResponse(content=json.dumps(students))

def sendTodayTakenCourses(r: HttpRequest):
    theDay = datetime.datetime.today().strftime('%A').lower()
    tutor = models.tutors.objects.filter(tutorID=r.session['userID']).first()
    courses = list(models.timeTableclassDistribution.objects.filter(
        timeTableSelector__department__departmentID = tutor.tutorDepartment.departmentID,
        day = theDay,
        course__taughtBy__tutorID = tutor.tutorID
    ).annotate(
        ID = Cast('course__courseID', output_field=fields.CharField()),
        TTDID = Cast('timeTableSelector__timeTableID', output_field=fields.CharField()),
    ).values('ID', 'course__courseName', 'TTDID', 'day'))
    return HttpResponse(content=json.dumps(courses))

def storeAttendance(r: HttpRequest):
    input = json.loads(r.body.decode('utf-8'))
    clasinfo = models.timeTableclassDistribution.objects.filter(
        course__courseID = input['course'],
        timeTableSelector__timeTableID = input['TTDID'],
        day = input['day']
    ).first()
    takenCourse = models.courses.objects.filter(courseID = input['course']).first()
    if models.classes.objects.filter(
        takenCourse = clasinfo.course,
        date = datetime.date.today(),
        classSessionStart = clasinfo.sessionStart,
        classSessionEnd = clasinfo.sessionEnd,
    ).exists():
        return HttpResponse(content=json.dumps({'message': 'already stored'}))
    clas = models.classes()
    clas.classSessionStart = clasinfo.sessionStart
    clas.classSessionEnd = clasinfo.sessionEnd
    clas.tutorPresent = 1
    clas.date = datetime.date.today()
    clas.takenCourse = takenCourse
    clas.tutor = models.tutors.objects.filter(tutorID = r.session['userID']).first()
    clas.save()
    data = []
    for student in input['data']:
        data.append(models.attendance(
            ofClass = clas,
            ofStudent = models.students.objects.filter(studentID = student['ID']).first(),
            present = student['present']
        ))
    models.attendance.objects.bulk_create(data)
    return HttpResponse(json.dumps({'message': 'positive'}))


def pinLeaveRequest(r: HttpRequest):
    lecure = models.courses.objects.filter(courseName=json.loads(r.body.decode('utf-8'))['lectureName']).first()
    student = models.students.objects.filter(studentID=r.session['userID']).first()
    if models.leaveRequests.objects.filter(
        byStudent__studentID = r.session['userID'],
        forCourse = lecure,
        forDate = json.loads(r.body.decode('utf-8'))['forDate']
    ).exists():
        models.leaveRequests.objects.filter(
        byStudent__studentID = r.session['userID'],
        forCourse = lecure,
        forDate = json.loads(r.body.decode('utf-8'))['forDate']).first().reason = json.loads(r.body.decode('utf-8'))['reason']
        return HttpResponse(content=json.dumps({'message': 'success'}))
    LRrecord = models.leaveRequests()
    LRrecord.byStudent = student
    LRrecord.forCourse = lecure
    LRrecord.forDate = json.loads(r.body.decode('utf-8'))['forDate']
    LRrecord.statusI = 'pending'
    LRrecord.statusII = 'pending'
    LRrecord.reason = json.loads(r.body.decode('utf-8'))['reason']
    LRrecord.save()
    return HttpResponse(content=json.dumps({'message': 'success'}))


def adminVibeCheck(r: HttpRequest):
    userName = json.loads(r.body.decode('utf-8'))['username']
    password = json.loads(r.body.decode('utf-8'))['password']
    passKey = json.loads(r.body.decode('utf-8'))['passKey']
    user = models.admins.objects.filter(
        username = userName,
        passWord = password,
        secureKey = passKey
    )
    if not user.exists():
        return HttpResponse(content=json.dumps({'message': 'negative'}))
    else:
        r.session['adminID'] = user.first().deanOf.departmentID.__str__()
        return HttpResponse(content=json.dumps({'message': 'success'}))


def sendAdminName(r: HttpRequest):
    name = models.departments.objects.filter(
        departmentID = r.session['adminID']
    ).first().dean

    return HttpResponse(content=json.dumps({'name': name}))

@transaction.atomic
def storeBuchOfStudents(r: HttpRequest):
    data = json.loads(r.body.decode('utf-8'))
    keys = list(dict(data[0]).keys())
    for student in data:
        try:
            s = models.students()
            s.studentFirstName = student[keys[0]]
            s.studentLastName = student[keys[1]]
            department = models.departments.objects.filter(
                departmentName = student[keys[2]]
            )
            if not department.exists():
                raise models.departments.DoesNotExist('no department named \"{}\" in student {}'.format(student[keys[2]], (student[keys[0]] + ' ' + student[keys[1]])))
            s.fromDepartment = department.first()
            s.major = student[keys[3]]
            s.stage = student[keys[4]]
            s.full_clean()
            s.save()
        except Exception as error:
            return HttpResponse(content=json.dumps({'message': str(error)}))
    return HttpResponse(content=json.dumps({'message': 'success'}))

def logAdminOut(r: HttpRequest):
    print('x')
    if not r.session.exists(r.COOKIES.get('sessionid')):
        return HttpResponse(content=json.dumps({'message': 'negative'}))
    cookies = r.COOKIES.keys()
    r.session.flush()
    r.session.set_expiry(0)
    r.session.clear()
    response = HttpResponse(content=json.dumps({'message': 'positive'}))
    for key in cookies:
        response.delete_cookie(key)
    return HttpResponse(content=json.dumps({'message': 'positive'}))


def logUserOut(r: HttpRequest):
    if not r.session.exists(r.COOKIES.get('sessionid')):
        return HttpResponse(content=json.dumps({'message': 'negative'}))
    cookies = r.COOKIES.keys()
    r.session.flush()
    r.session.set_expiry(0)
    r.session.clear()
    response = HttpResponse(content=json.dumps({'message': 'positive'}))
    for key in cookies:
        response.delete_cookie(key)
    return HttpResponse(content=json.dumps({'message': 'positive'}))