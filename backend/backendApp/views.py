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

def findWeeklyPrecense(r: HttpRequest):
    allRecords = models.attendance.objects.filter(
        ofStudent = r.session['userID'],
        ofClass__takenCourse__year = models.students.objects.filter(studentID=r.session['userID']).first().stage,
    )
    weeklyPresence = []

    precensePerWeek = 0
    for i in range(len(allRecords)):
        precensePerWeek += allRecords[i].present
        if i % 5 == 0:
            weeklyPresence.append((precensePerWeek/5) * 100)
            precensePerWeek = 0

    return sum(weeklyPresence) / len(weeklyPresence)

def findWeeklyPrecenseT(r: HttpRequest):
    allRecords = models.attendance.objects.filter(
        ofClass__tutor__tutorID = r.session['userID'],
    )
    weeklyPresence = []

    precensePerWeek = 0
    for i in range(len(allRecords)):
        precensePerWeek += allRecords[i].present
        if i % 5 == 0:
            weeklyPresence.append((precensePerWeek/5) * 100)
            precensePerWeek = 0

    return sum(weeklyPresence) / len(weeklyPresence)


def findMonthlyPresencePercentage(r: HttpRequest):
    presencePerMonth = []
    eachMonthPresence = 0
    stage = int(models.students.objects.filter(studentID=r.session['userID']).first().stage)
    for month in [x for x in range(1, 13)]:
        areThereRecords = models.attendance.objects.filter(
            ofStudent=r.session['userID'],
            ofClass__takenCourse__year = stage,
            ofClass__date__month=month).count()
        
        if areThereRecords == 0:
            continue


        monthlyRevisionOfpresence = models.attendance.objects.filter(
            ofStudent=r.session['userID'],
            ofClass__takenCourse__year = stage,
            present=1,
            ofClass__date__month=month).count()

        monthlyRevisionOfclasses = models.attendance.objects.filter(
            ofStudent=r.session['userID'],
            ofClass__takenCourse__year = stage,
            ofClass__date__month=month).count()

        if monthlyRevisionOfclasses == 0:
            continue
        eachMonthPresence = (monthlyRevisionOfpresence / monthlyRevisionOfclasses) * 100
        presencePerMonth.append(eachMonthPresence)
        eachMonthPresence = 0
    print(presencePerMonth)
    return sum(presencePerMonth) / len(presencePerMonth)

def findMonthlyPresencePercentageT(r: HttpRequest):
    presencePerMonth = []
    eachMonthPresence = 0
    for month in [x for x in range(1, 13)]:
        areThereRecords = models.attendance.objects.filter(
            ofClass__tutor__tutorID = r.session['userID'],
             ofClass__date__month=month
            ).count()
        
        if areThereRecords == 0:
            continue


        monthlyRevisionOfpresence = models.attendance.objects.filter(
            ofClass__tutor__tutorID = r.session['userID'],
            present=1,
            ofClass__date__month=month
            ).count()

        monthlyRevisionOfclasses = models.attendance.objects.filter(
            ofClass__tutor__tutorID = r.session['userID'],
            ofClass__date__month=month
            ).count()

        if monthlyRevisionOfclasses == 0:
            continue
        eachMonthPresence = (monthlyRevisionOfpresence / monthlyRevisionOfclasses) * 100
        presencePerMonth.append(eachMonthPresence)
        eachMonthPresence = 0
    print(presencePerMonth)
    return sum(presencePerMonth) / len(presencePerMonth)

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
    if r.COOKIES.get('csrftoken') is None:
        resp = HttpResponse()
        resp.set_cookie('csrftoken', get_token(r), 1209800, path='/')
        return HttpResponse({})
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
    if r.session['userID'] is None:
        return HttpResponse(content=json.dumps({'message': 'negative'}))
    if r.session['role'] is None:
        return HttpResponse(content=json.dumps({'message': 'negative'}))
    if r.session['role'] == 'S':
        return HttpResponse(content=json.dumps({'message': 'S'}))
    if r.session['role'] == 'T':
        return HttpResponse(content=json.dumps({'message': 'T'}))

def amIAValid(r: HttpRequest):
    if r.session.session_key is None:
         return HttpResponse(content=json.dumps({'message': 'negative'}))
    if r.session['userID'] is None:
         return HttpResponse(content=json.dumps({'message': 'negative'}))
    if r.session['role'] is None or r.session['role'] is not json.loads(r.body.decode('utf-8'))['role']:
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
        monthlyPresence = findMonthlyPresencePercentageT(r)
        weeklyPresence = findWeeklyPrecenseT(r)
    elif r.session['role'] is 'S':
        monthlyPresence = findMonthlyPresencePercentage(r)
        weeklyPresence = findWeeklyPrecense(r)

    return HttpResponse(content=json.dumps({
        'weeklyPresence': weeklyPresence,
        'monthlyPresence': monthlyPresence
    }))

def sendStudentAttendanceStats(r: HttpRequest):
    student = models.students.objects.filter(
        studentID = r.session['userID']
    ).first()
    data = list(models.attendance.objects.filter(
        ofStudent=r.session['userID'],
        ofClass__takenCourse__year = student.stage,
        present=0
        ).annotate(
            date = Cast('ofClass__date', fields.CharField()),
            course = Cast('ofClass__takenCourse__courseName', fields.CharField()),
        ).values('course', 'date'))
    return HttpResponse(content=json.dumps(data))

# def sendTeacherData(r: HttpRequest):
#     data['leaveRequests'] = list(models.leaveRequests.objects.filter(
#         forCourse__taughtBy__tutorID = r.session['userID']
#     ).annotate(
#         student = Concat('byStudent__studentFirstName', Value(' '), 'byStudent__studentLastName', output_field=fields.CharField()),
#         studentID = Cast('byStudent__studentID', fields.CharField()),
#         date = Cast('forDate', fields.CharField()),
#         courseID = Cast('forCourse__courseID', fields.CharField()),
#         courseName = Cast('forCourse__courseName', fields.CharField()),
#     ).values('student', 'studentID', 'date', 'courseID', 'courseName'))
    

#     courses = models.courses.objects.filter(
#         taughtBy__tutorID = r.session['userID'],
#     )
#     data['storeAttendance'] = {}
#     for course in courses:
#         data['storeAttendance'][course.courseName] = list(models.students.objects.filter(
#             stage = course.year,
#             fromDepartment = course.byDepartment.departmentID
#         ).annotate(
#             student = Concat('studentFirstName', Value(' '), 'studentLastName', output_field=fields.CharField()),
#             ID = Cast('studentID', fields.CharField()),
#         ).values('student', 'ID', 'stage'))
    
#     x = HttpResponse()
#     x.set_cookie('data', json.dumps(data['weeklyPresence']))
#     x.set_cookie('data', json.dumps(data['monthlyPresence']))
#     x.set_cookie('data', json.dumps(data['leaveRequests']))
#     x.set_cookie('data', json.dumps(data['']))
#     return HttpResponse(content={})

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

def sendAttendanceRecords(r: HttpRequest):
    fromDate = json.loads(r.body.decode('utf-8'))['fromDate']
    toDate = json.loads(r.body.decode('utf-8'))['toDate']
    course = json.loads(r.body.decode('utf-8'))['course']
    data = list(
        models.attendance.objects.filter(
        ofClass__takenCourse__courseID = course,
        present = 0,
        ofClass__date__gte = fromDate,
        ofClass__date__lte = toDate
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

    return HttpResponse(content=json.dumps(data))


def sendAttendanceHistoryToTeacher(r: HttpRequest):
    data = {}
    data['precenceStages'] = []
    data['studentAttendance'] = {}
    for stage in range(1, 5):
        course = models.courses.objects.filter(
            taughtBy__tutorID = r.session['userID'],
            year = stage
        )

        if course.exists() == 0:
            continue

        if models.attendance.objects.filter(ofClass__tutor__tutorID = r.session['userID'], ofClass__takenCourse__courseID = course.first().courseID).count() == 0:
            continue

        data['precenceStages'].append(stage)
        data['studentAttendance'][stage] = list(models.attendance.objects.filter(
            ofClass__tutor__tutorID = r.session['userID'],
            ofClass__takenCourse__courseID = course.first().courseID,
            present=0
        ).annotate(
            student = Concat('ofStudent__studentFirstName', Value(' '), 'ofStudent__studentLastName', output_field=fields.CharField()),
            course = Cast('ofClass__takenCourse__courseName', fields.CharField()),
        ).values('student', 'course', 'present'))
    return HttpResponse(content=json.dumps(data))


def pinLeaveRequest(r: HttpRequest):
    print(json.loads(r.body.decode('utf-8'))['lectureName'])
    lecure = models.courses.objects.filter(courseName=json.loads(r.body.decode('utf-8'))['lectureName']).first()
    student = models.students.objects.filter(studentID=r.session['userID']).first()
    LRrecord = models.leaveRequests()
    LRrecord.byStudent = student
    LRrecord.forCourse = lecure
    LRrecord.forDate = json.loads(r.body.decode('utf-8'))['forDate']
    LRrecord.statusI = 'pending'
    LRrecord.statusII = 'pending'
    LRrecord.reason = json.loads(r.body.decode('utf-8'))['reason']
    LRrecord.save()
    return HttpResponse(content=json.dumps({'message': 'success'}))
