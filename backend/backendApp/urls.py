from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login),
    path('logOut', views.logUserOut),
    path('csrf', views.loadcsrf),
    path('pullName', views.sendName),
    path('amILogedIn', views.amILogedIn),
    path('authorise', views.amIAValid),
    path('pullPercentages', views.sendWeekMonth),
    path('storeLeaveRequest', views.pinLeaveRequest),
    path('pullMyCourses', views.sendTakenCoursesToStudent),
    path('pullTableData', views.sendTableDataToStudent),
    path('pullMyStats', views.sendStudentAttendanceStats),
    path('pullMyLeaveRequests', views.studentLeaveRequestsHistory),
    path('pullTimeTable', views.sendStudentTimeTable),
    path('pullAvailableCourses', views.sendAvailableCoursesToTeacher),
    path('pullRecords', views.sendAttendanceRecords),
    path('adminLogin', views.adminVibeCheck),
    path('pullStudentsForAttendanceInput', views.sendStudentsForAttendanceInput),
    path('pullTodayCourse', views.sendTodayTakenCourses),
    path('sendAttendance', views.storeAttendance),
    path('pullLeaveRequestsT', views.sendleaveRequestsToTeacher),
    path('teacherRespondToLeaveReq', views.updateLeaveRequest),
    path('getAdminName', views.sendAdminName),
    path('storeStudentsInBulk', views.storeBuchOfStudents),
    path('adminLogOut', views.logAdminOut),
]