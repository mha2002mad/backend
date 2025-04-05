from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login),
    path('csrf', views.loadcsrf),
    path('amILogedIn', views.amILogedIn),
    path('authorise', views.amIAValid),
    path('pullPercentages', views.sendWeekMonth),
    path('storeLeaveRequest', views.pinLeaveRequest),
    path('pullMyStats', views.sendStudentAttendanceStats),
    path('pullMyLeaveRequests', views.studentLeaveRequestsHistory),
    path('pullTimeTable', views.sendStudentTimeTable),
    path('pullAvailableCourses', views.sendAvailableCoursesToTeacher),
    path('pullRecords', views.sendAttendanceRecords),
    path('pullAttendanceStats', views.sendAttendanceHistoryToTeacher), #?????
    path('pullStudentsForAttendanceInput', views.sendStudentsForAttendanceInput),
    path('pullTodayCourse', views.sendTodayTakenCourses),
    path('sendAttendance', views.storeAttendance),
    path('pullLeaveRequestsT', views.sendleaveRequestsToTeacher),
    path('teacherRespondToLeaveReq', views.updateLeaveRequest),
]