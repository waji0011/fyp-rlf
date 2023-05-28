from django.contrib import admin
from .models import Profile, Video, Challan, contact, userdata, QuizScore

class VideoInline(admin.TabularInline):
    model = Video
    extra=0
class QuizScoreInline(admin.TabularInline):
    model = QuizScore
    extra=0
class ChallanInline(admin.TabularInline):
    model = Challan
    extra=0
admin.site.register(contact)
class UserDataInline(admin.StackedInline):
    model = userdata
    extra=0

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    inlines = [VideoInline, ChallanInline, UserDataInline, QuizScoreInline]

    