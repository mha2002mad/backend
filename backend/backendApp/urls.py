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
    path('pullAttendanceStats', views.sendAttendanceHistoryToTeacher),
]