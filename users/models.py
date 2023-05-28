from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


# Extending User Model Using a One-To-One Link
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    has_submitted_registration_form = models.BooleanField(default=False)
    has_submitted_video = models.BooleanField(default=False)
    has_submitted_challan = models.BooleanField(default=False)
    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    bio = models.TextField()
    Learner_issue = models.DateField(null=True, blank=True)
    learner_expire = models.DateField(null=True, blank=True)
    Physical_test_passed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    # resizing images
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.avatar.path)

        if img.height > 100 or img.width > 100:
            new_img = (100, 100)
            img.thumbnail(new_img)
            img.save(self.avatar.path)
    def renew_license(self):
        if self.Physical_test_passed:
            today = timezone.now().date()
            self.Learner_issue = today
            self.learner_expire = today + timezone.timedelta(days=10)
            self.save()

    
    def save(self, request, *args, **kwargs):
        is_new_profile = self.pk is None

        super().save(*args, **kwargs)

        if is_new_profile and not self.is_active:
            current_site = get_current_site(request)
            mail_subject = 'Activate your account'
            message = render_to_string('users/activation_email.html', {
                'user': self.user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(self.user.pk)),
                'token': default_token_generator.make_token(self.user),
            })
            send_mail(
                mail_subject,
                strip_tags(message),
                settings.DEFAULT_FROM_EMAIL,
                [self.user.email],
                html_message=message
            )
    
            
# Video model to represent a video file
class Video(models.Model):  
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    video = models.FileField(upload_to='media/videos_uploaded')
    verified = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    score = models.CharField(default='',max_length=5)
    
    def __str__(self):
        return f'{self.profile.user.username} - {self.video.name}'
    def save(self, *args, **kwargs):
        # Check if the `verified` or `rejected` fields have changed
        if self.pk and (self.verified != self.__class__.objects.get(pk=self.pk).verified
                        or self.rejected != self.__class__.objects.get(pk=self.pk).rejected):
            # Determine the subject and message for the email notification
            subject = 'Sign Test Status'
            if self.verified:
                message = 'Your Sign Test has been verified.'
            elif self.rejected:
                message = 'Your Sign Test Not Passed'
            else:
                # No need to send an email if neither verified nor rejected
                return

            # Render the HTML email template with the message
            html_message = render_to_string('users/challan_notification.html', {'message': message})

            # Create a plain text version of the email
            plain_message = strip_tags(html_message)

            # Retrieve the user's email address from the related `Profile` object
            user_email = self.profile.user.email

            # Send the email notification
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user_email],
                html_message=html_message
            )

        # Save the `Challan` object
        super().save(*args, **kwargs)
    
class QuizScore(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    score = models.IntegerField()
    def str(self):
        return self.profile.user.username


# Challan model to represent a traffic challan
class Challan(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='challan_images/')
    verified = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    verified_date = models.DateTimeField(default=timezone.now)
    user_message = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return f'{self.profile.user.username} - {self.image.name}'
    def save(self, *args, **kwargs):
        # Check if the `verified` or `rejected` fields have changed
        if self.pk and (self.verified != self.__class__.objects.get(pk=self.pk).verified
                        or self.rejected != self.__class__.objects.get(pk=self.pk).rejected):
            # Determine the subject and message for the email notification
            subject = 'Challan Status '
            if self.verified:
                message = 'Your challan has been verified.'
            elif self.rejected:
                message = 'Your challan has been rejected'
            else:
                # No need to send an email if neither verified nor rejected
                return

            # Render the HTML email template with the message
            html_message = render_to_string('users/challan_notification.html', {'message': message})

            # Create a plain text version of the email
            plain_message = strip_tags(html_message)

            # Retrieve the user's email address from the related `Profile` object
            user_email = self.profile.user.email

            # Send the email notification
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user_email],
                html_message=html_message
            )

        # Save the `Challan` object
        super().save(*args, **kwargs)

class contact(models.Model):
    Fullname = models.CharField(max_length=255,default='')
    Email = models.CharField(max_length=255)
    Subject = models.CharField(max_length=255)
    Message = models.TextField()
    def send_email(self):
        subject = 'Contact Form Submission'
        message = f'Name: {self.Fullname}\nEmail: {self.Email}\nSubject: {self.Subject}\nMessage: {self.Message}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [self.Email] 
        send_mail(subject, message, from_email, to_email, fail_silently=False)
    

# UserData model to store user information
class userdata(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    Fullname = models.CharField(max_length=255, default='')
    Fathername = models.CharField(max_length=255, default='')
    cnic = models.CharField(max_length=15)
    challanid = models.CharField(max_length=15, default='')
    dob = models.DateField(default=timezone.now)
    gender = models.CharField(max_length=6, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    height = models.CharField(max_length=255, default='')
    blood_group = models.CharField(max_length=3, choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')])
    challan_file = models.FileField(upload_to='pdf_files/', blank=True, null=True, default='')
    learner_file = models.FileField(upload_to='pdf_files/', blank=True, null=True, default='')
    submission_date = models.DateTimeField(default=timezone.now)
    address = models.CharField(max_length=255, default='')
    profile_picture = models.ImageField(upload_to='profile_pictures', blank=True, null=True)
    front_cnic_picture = models.ImageField(upload_to='cnic_pictures', blank=True, null=True)
    back_cnic_picture = models.ImageField(upload_to='cnic_pictures', blank=True, null=True)

    def __str__(self):
        return self.profile.user.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
