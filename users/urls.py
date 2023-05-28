

from django.urls import path
from .views import home, profile, contactus, registration, RegisterView,renew_license, theorytest,upload_challan,challan_detail,challan_view,upload_video,download_pdf,generate_pdf,verify_license
from . import views
urlpatterns = [
    path('', home, name='users-home'),
    path('register/', RegisterView.as_view(), name='users-register'),
    path('profile/', profile, name='users-profile'),
    path('registration/',registration, name='registration'),
    path('contactus/',contactus, name='contactus'),
    path('theorytest/',theorytest, name='theorytest'),
    # path('fees/',fees, name='fees'),
    path('upload-challan/', upload_challan, name='upload_challan'),
    path('challan_detail/', challan_detail, name='challan_detail'),
    path('challan/', views.challan_view, name='challan'),
    # path('challan/<int:challan_id>/pdf/', views.generate_pdf, name='generate_pdf'),
    # path('video_verify/', views.video_verify, name='video_verify'),
    path('video/', views.video_view, name='video'),
    path('upload_video/', views.upload_video, name='upload_video'),
    path('video_status/', views.video_status, name='video_status'),
    path('download-pdf/', download_pdf, name='download_pdf'),
    path('generate_pdf', generate_pdf, name='generate_pdf'),
    path('verify_license/', verify_license, name='verify_license'),
    path("save_score/", views.save_score, name="save_score"),
    path('renew_license/', renew_license, name='renew_license'),
] 
