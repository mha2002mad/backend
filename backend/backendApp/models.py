import dbm.dumb
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
import uuid
import datetime

"""

"""


class departments(models.Model):
    departmentID = models.UUIDField(name='departmentID', default=uuid.uuid4, primary_key=True, auto_created=True, unique=True, null=False)
    departmentName = models.CharField(name='departmentName', unique=True, null=False)
    dean = models.CharField(name='dean', null=False, unique=True)
    class meta:
        db_table = 'departments'

class students(models.Model):
    studentID = models.UUIDField(name='studentID', default=uuid.uuid4, primary_key=True, auto_created=True, unique=True, null=False)
    studentFirstName = models.CharField(name='studentFirstName', null=False)
    studentLastName = models.CharField(name='studentLastName', null=False)
    major = models.CharField(name='major', null=False, max_length=32)
    fromDepartment = models.ForeignKey(departments,related_name='fromDepartment', to_field='departmentID', on_delete=models.CASCADE)
    stage = models.IntegerField(name='stage', null=False, validators=[
        MinValueValidator(1),
        MaxValueValidator(6)
    ], default=1)
    class meta:
        db_table = 'students'

class studentCredentials(models.Model):
    forStudent = models.ForeignKey(students, to_field='studentID', related_name='forStudent', on_delete=models.CASCADE, null=False, unique=True)
    studentUserName = models.CharField(name='studentUserName', null=False, unique=True)
    studentPassword = models.CharField(name='studentPassword', unique=False, null=False)

class tutors(models.Model):
    tutorID = models.UUIDField(name='tutorID', default=uuid.uuid4, primary_key=True, auto_created=True, unique=True, null=False)
    tutorFirstName = models.CharField(name='tutorFirstName', null=False)
    tutorLastName = models.CharField(name='tutorLastName', null=False)
    tutorEmail = models.EmailField(name='tutorEmail', unique=True, null=False)
    tutorDepartment = models.ForeignKey(departments, related_name='tutorDepartment', to_field='departmentID', null=False, on_delete=models.PROTECT)
    class meta:
        db_table = 'tutors'

class tutorCredentials(models.Model):
    forTutor = models.ForeignKey(tutors, to_field='tutorID', related_name='forTutor', on_delete=models.CASCADE, null=False, unique=True)
    tutorUserName = models.CharField(name='tutorUserName', null=False, unique=True)
    tutorPassword = models.CharField(name='tutorPassword', unique=False, null=False)

class courses(models.Model):
    courseID = models.UUIDField(name='courseID', default=uuid.uuid4, primary_key=True, auto_created=True, unique=True, null=False)
    courseName = models.CharField(name='courseName', unique=True, null=False)
    year = models.IntegerField(name='year', null=False, validators=[
        MinValueValidator(1),
        MaxValueValidator(6)
    ])
    semster = models.IntegerField(name='semster', null=False, choices=[(1, '1'), (2, '2')])
    taughtBy = models.ForeignKey(tutors, related_name='taughtBy', to_field='tutorID', null=False, unique=False, on_delete=models.PROTECT)
    byDepartment = models.ForeignKey(departments, related_name='byDepartment', to_field='departmentID', null=False, on_delete=models.PROTECT)
    class meta:
        db_table = 'courses'

class classes(models.Model):
    classID = models.UUIDField(name='classID', default=uuid.uuid4, primary_key=True, auto_created=True, unique=True, null=False)
    date = models.DateField(name='date', null=False, auto_created=True)
    classSessionStart = models.TimeField(name='classSessionStart', validators=[
        MinValueValidator(datetime.time(8, 30, 0)),
        MaxValueValidator(datetime.time(18, 0, 0))
    ], null=False)
    classSessionEnd = models.TimeField(name='classSessionEnd', validators=[
        MaxValueValidator(datetime.time(20, 0, 0))
    ], null=False)
    tutorPresent = models.IntegerField(name='tutorPresent', null=False, choices=[(0, '0'), (1, '1')])
    takenCourse = models.ForeignKey(courses, related_name='takenCourse', to_field='courseID', null=False, on_delete=models.PROTECT)
    tutor = models.ForeignKey(tutors, related_name='tutor', to_field='tutorID', null=False, on_delete=models.PROTECT)
    class meta:
        db_table = 'classes'

class attendance(models.Model):
    present = models.IntegerField(name='present', null=False, choices=[(0, '0'), (1, '1')])
    ofClass = models.ForeignKey(classes, related_name='ofClass', to_field='classID', null=False, on_delete=models.CASCADE)
    ofStudent = models.ForeignKey(students, related_name='ofStudent', to_field='studentID', null=False, on_delete=models.PROTECT)
    class meta:
        db_table = 'attendance'
        unique_together = ('ofClass', 'ofStudent')

class admins(models.Model):
    userName = models.CharField(name='username', primary_key=True, unique=True, null=False)
    passWord = models.CharField(name='passWord', null=False)
    deanOf = models.ForeignKey(departments, related_name='deanOf', to_field='departmentID', on_delete=models.CASCADE, default='a5b4705d-929b-46c0-b911-fe5e60fcd75c')
    secureKey = models.CharField(name='secureKey', null=False, default='')
    class meta:
        db_table = 'admins'

class timeTable(models.Model):
    timeTableID = models.UUIDField(name='timeTableID', primary_key=True, unique=True, null=False, default=1)
    department = models.ForeignKey(departments, related_name='department', to_field='departmentID', null=False, on_delete=models.CASCADE)
    stage = models.IntegerField(name='stage', null=False, validators=[
        MinValueValidator(1),
        MaxValueValidator(6)
    ], default=1)

class timeTableclassDistribution(models.Model):
    timeTableSelector = models.ForeignKey(timeTable, related_name='timeTableSelector', to_field='timeTableID', unique=False, null=False, on_delete=models.CASCADE)
    day = models.CharField(name='day', null=False, choices=[
        ('sunday', 'sunday'),
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),]
        )
    course = models.ForeignKey(courses, related_name='course', to_field='courseID', null=False, on_delete=models.CASCADE)
    sessionStart = models.TimeField(name='sessionStart', validators=[
        MinValueValidator(datetime.time(8, 30, 0)),
        MaxValueValidator(datetime.time(18, 0, 0))
    ], null=False)
    sessionEnd = models.TimeField(name='sessionEnd',validators=[
        MaxValueValidator(datetime.time(20, 0, 0))
    ], null=False)
    class meta:
        db_table = 'timeTableclassDistribution'
 
class leaveRequests(models.Model):
    byStudent = models.ForeignKey(students, related_name='byStudent', to_field='studentID', null=False, on_delete=models.CASCADE)
    forDate = models.DateField(name='forDate', null=False, validators=[MinValueValidator(datetime.datetime.now().date())])
    forCourse = models.ForeignKey(courses, to_field='courseID', related_name='forCourse', null=False, on_delete=models.CASCADE, default='6d1fb8cf-8201-4292-b53b-c0c4057f35d5')
    reason = models.TextField(name='reason', null=False)
    statusI = models.CharField(name='statusI', null=False, choices=[
        ('pending', 'pending'),
        ('approved', 'approved'),
        ('rejected', 'rejected')
        ], default='pending')
    statusII = models.CharField(name='statusII', null=False, choices=[
        ('pending', 'pending'),
        ('approved', 'approved'),
        ('rejected', 'rejected')
        ], default='pending')
    class meta:
        db_table = 'leaveRequests'
