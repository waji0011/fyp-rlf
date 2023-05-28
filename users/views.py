
from django.shortcuts import get_object_or_404, render, redirect
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm, UpdateUserForm, UpdateProfileForm
from users.models  import Challan,Video,userdata,contact,Profile,QuizScore
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, inch
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
import io
from reportlab.lib.units import inch
from django.contrib import admin
from django.core.files.base import ContentFile
from django.http import JsonResponse
from .models import Profile, Video
from django.core.files.storage import default_storage
import os
import re
import json
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.shortcuts import render
import random
from django.templatetags.static import static
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator



from datetime import datetime, timedelta
def renew_license(request):
    profile = request.user.profile

    if request.method == 'POST':
        profile.learner_expire = datetime.today() + timedelta(days=10)
        profile.save()
        return redirect('renew_license')  # Redirect to the renew_license page
    else:
        today = datetime.today().date()
        return render(request, 'users/renew_license.html', {'profile': profile, 'today': today})

# class VideoAdmin(admin.ModelAdmin):
#     list_display = [ 'user', 'video', 'verified']
#     actions = ['verify_videos']

def verify_videos(self, request, queryset):
        queryset.update(verified=True)
        self.message_user(request, "Selected videos have been verified.")
verify_videos.short_description = "Verify selected videos"



def upload_video(request):
    if request.method == 'POST':
        video_file = request.FILES['video']
        file_name = default_storage.save('videos/' + video_file.name, ContentFile(video_file.read()))
        quiz_score = QuizScore.objects.filter(profile=request.user.profile).last()
        score = quiz_score.score if quiz_score else ''
        video = Video.objects.create(video=file_name, profile=request.user.profile,score=score)
        request.user.profile.has_submitted_video = True
        request.user.profile.save()
        video.save()
        return redirect('upload_video')
    if Video.objects.filter(profile=request.user.profile, rejected=True).exists():
        profile = request.user.profile
        profile.has_submitted_video = False
        profile.save()
        Video.objects.filter(profile=profile, rejected=True).delete()
        return render(request, 'users/upload_video.html', {"profile": profile})
    return render(request, 'users/upload_video.html')
def save_score(request):
    if request.method == "POST":
        data = json.loads(request.body)
        score = data.get("score")
        quiz_score = QuizScore(profile=request.user.profile, score=score)
        quiz_score.save()
        return JsonResponse({ "score": score })
    else:
        return JsonResponse({ "error": "Invalid request method." })

def video_status(request):
    video = Video.objects.filter(profile=request.user.profile).last()
    if request.method == 'POST' and request.POST.get('verify'):
        video.verified = True
        video.save()
        messages.success(request, 'Your video has been verified and is now available for viewing.')
        return redirect('video') # redirect to video template
    context = {
        'video': video,
    }
    return render(request, 'users/video.html', context)

def video_view(request):
    video = Video.objects.filter(profile=request.user.profile).last()
    if request.method == 'GET':
        if 'remaining_days' not in request.session:
            return redirect('challan_detail')  # Redirect to challan_detail if challan details are not available in session
            
        remaining_days = request.session.get('remaining_days')
        remaining_hours = request.session.get('remaining_hours')
        remaining_minutes = request.session.get('remaining_minutes')
        return render(request, 'users/video.html', {
            'remaining_days': remaining_days,
            'remaining_hours': remaining_hours,
            'remaining_minutes': remaining_minutes,
            'profile': request.user.profile,
            'video': video}
        )


def challan_view(request):
    context = {
        'challan': request.user.profile.challan_set.last()
    }
    return render(request, 'users/challan.html', context)


# def verify_challan(self, request, queryset):
#         queryset.update(verified=True)
#         for challan in queryset:
#             if challan.user_message:
#                 messages.success(request, challan.user_message)
# verify_challan.short_description = 'Verify selected challans'

# actions = [verify_challan]

# admin.site.register(Challan, ChallanAdmin)


def challan_detail(request):
    challan = Challan.objects.filter(profile=request.user.profile).last()

    if challan is not None and challan.verified:
        eligible_date = challan.verified_date + timedelta(days=5)
        remaining_time = eligible_date - timezone.now()
        remaining_days= remaining_time.days
        remaining_hours, remaining_minutes = divmod(remaining_time.seconds // 60, 60)
        request.session['remaining_days'] = remaining_days
        request.session['remaining_hours'] = remaining_hours
        request.session['remaining_minutes'] = remaining_minutes
        context = {
            'challan': challan,
            'remaining_days': remaining_days,
            'remaining_hours': remaining_hours,
            'remaining_minutes': remaining_minutes,
        }
    
    elif request.method == 'POST' and request.POST.get('reject'):
        challan.rejected = True
        request.user.profile.has_submitted_challan = False
        request.user.profile.save()
        challan.save()
    else:
        context = {
            'challan': challan,
        }
    return render(request, 'users/challan_detail.html',  context)


def home(request):
    return render(request, 'users/home.html')

def theorytest(request):
    return render(request, 'users/theorytest.html')

def user_data_view(request):
    user_data = userdata.objects.all()
    context = {'user_data': user_data}
    return render(request, 'users/user_data.html', context)

def verify_license(request):
    if request.method == 'GET':
        cnic = request.GET.get('cnic', '')
        try:
            userdata_obj = userdata.objects.get(cnic=cnic)
        except userdata.DoesNotExist:
            userdata_obj = None
        except MultipleObjectsReturned:
            userdata_obj = userdata.objects.filter(cnic=cnic).last()
        return render(request, 'users/verify_license.html', {'userdata': userdata_obj})
    return render(request, 'users/verify_license.html')
    
def upload_challan(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        challan = Challan.objects.create(image=image, profile=request.user.profile)
        request.user.profile.has_submitted_challan = True
        request.user.profile.save()
        return redirect('challan_detail')
    return render(request, 'users/upload_challan.html')


from django.core.files.storage import FileSystemStorage
def registration(request):
    n = ''
    if request.method == 'POST':
        name = request.POST.get('name')
        cnic = request.POST.get('cnic')
        fname = request.POST.get('fname')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        bloodgroup = request.POST.get('bloodgroup')
        feet = request.POST.get('feet')
        inches = request.POST.get('inches')
        address = request.POST.get('address')
        profile_picture = request.FILES.get('profile_picture')
        front_cnic_picture = request.FILES.get('front_cnic_picture')
        back_cnic_picture = request.FILES.get('back_cnic_picture')
        # Save the files to the appropriate location
        fs = FileSystemStorage()
        # Check if a file was uploaded before attempting to save it
        if profile_picture:
            fs = FileSystemStorage(location='media/profile_pictures')
            profile_picture_filename = fs.save(profile_picture.name, profile_picture)
        else:
            profile_picture_filename = None

        if front_cnic_picture:
            fs = FileSystemStorage(location='media/cnic_pictures')
            front_cnic_picture_filename = fs.save(front_cnic_picture.name, front_cnic_picture)
        else:
            front_cnic_picture_filename = None

        if back_cnic_picture:
            fs = FileSystemStorage(location='media/cnic_pictures')
            back_cnic_picture_filename = fs.save(back_cnic_picture.name, back_cnic_picture)
        else:
            back_cnic_picture_filename = None
        # Calculate age based on date of birth
        birthdate = datetime.strptime(dob, '%Y-%m-%d').date()
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        height = feet+' Feet '+inches+' inches '
        challan_id = random.randint(100000, 999999)
        error_message = ''
        if age < 18:
            error_message = "You must be at least 18 years old to register"
        elif not re.match(r'^\d{5}-\d{7}-\d$', cnic):
            error_message = "Please enter a valid CNIC in the format 00000-0000000-0"

        if error_message:
            # Return error message and pre-fill form fields
            return render(request, 'users/registration.html', {'error_message': error_message,
                                                               'name': name,
                                                               'fname': fname,
                                                               'cnic': cnic,
                                                               'address ':address ,
                                                               'profile_picture':profile_picture,
                                                               'front_cnic_picture':front_cnic_picture,
                                                               'back_cnic_picture':back_cnic_picture,
                                                               'dob': dob,
                                                               'gender': gender,
                                                               'bloodgroup': bloodgroup,
                                                               'feet': feet,
                                                               'inches': inches,
                                                               'profile': request.user.profile})
        else:
            today = datetime.today()
            last_date = today + timedelta(days=90)
            elligible=today + timedelta(days=40)
             # Save the user's information to the database
            ab = userdata(profile=request.user.profile,Fullname=name,Fathername=fname, cnic=cnic, dob=dob, height=height, gender=gender, blood_group=bloodgroup,challanid=challan_id,address=address,
            profile_picture='profile_pictures/' + profile_picture_filename,
            front_cnic_picture='cnic_pictures/' + front_cnic_picture_filename,
            back_cnic_picture='cnic_pictures/' + back_cnic_picture_filename)
            ab.save()
            my_model = Profile.objects.get(id=request.POST.get("id2"))
            my_model.has_submitted_registration_form = True
            my_model.today = today
            my_model.last_date = last_date
            my_model.save()

            # Generate the bank challan using ReportLab
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="bank_challan.pdf"'
            buffer = io.BytesIO()
            # Create the PDF object using the buffer
            pdf = canvas.Canvas(buffer, pagesize=(8.5*inch, 11*inch))
            # Set up coordinates for drawing the user copy and bank copy
            user_x = 50
            bank_x = 400
            y = 750
            line_height = 15
            
            # Add a logo to the bank challan
            logo = settings.STATIC_ROOT + '\logo 3.png'
            pdf.drawImage(logo, 30, 780, width=100, height=100)
            # Draw the user copy
            pdf.setFont('Helvetica-Bold', 14)
            pdf.drawString(user_x, y, 'User Information')
            pdf.setFont('Helvetica', 12)
            
            pdf.drawString(user_x, y - line_height, 'Full Name: {}'.format(name))
            pdf.drawString(user_x, y - 2 * line_height, 'CNIC: {}'.format(cnic))
            pdf.drawString(user_x, y - 4 * line_height, 'Bank Details:')
            pdf.drawString(user_x, y - 5 * line_height, 'Bank Name: XYZ Bank')
            pdf.drawString(user_x, y - 6 * line_height, 'Branch: ABC Branch')
            pdf.drawString(user_x, y - 7 * line_height, 'Account No: 123456789')
            pdf.drawString(user_x, y - 8 * line_height, 'Fee: Rs 500')
            pdf.drawString(user_x, y - 9 * line_height, f'Date: {today.strftime("%Y-%m-%d")}')
            pdf.drawString(user_x, y - 10 * line_height, f'Valid Upto: {last_date.strftime("%Y-%m-%d")}')
            pdf.drawString(user_x, y - 11 * line_height, f'Challan ID: {challan_id}')
            # Draw the vertical line separator
            pdf.line(325, 0, 325, 1000)
            # Draw the bank copy
            pdf.setFont('Helvetica-Bold', 14)
            pdf.drawString(bank_x, y, 'Bank Copy')
            pdf.setFont('Helvetica', 12)
            pdf.drawString(bank_x, y - line_height, 'Full Name: {}'.format(name))
            pdf.drawString(bank_x, y - 2 * line_height, 'CNIC: {}'.format(cnic))
            pdf.drawString(bank_x, y - 4 * line_height, 'Bank Details:')
            pdf.drawString(bank_x, y - 5 * line_height, 'Bank Name: XYZ Bank')
            pdf.drawString(bank_x, y - 6 * line_height, 'Branch: ABC Branch')
            pdf.drawString(bank_x, y - 7 * line_height, 'Account No: 123456789')
            pdf.drawString(bank_x, y - 8 * line_height, 'Fee: Rs 500')
            pdf.drawString(bank_x, y - 9 * line_height, f'Date:{today.strftime("%Y-%m-%d")}')
            pdf.drawString(bank_x, y - 10 * line_height, f'Valid Upto: {last_date.strftime("%Y-%m-%d")}')
            pdf.drawString(bank_x, y - 11 * line_height, f'Challan ID: {challan_id}')
            # Save the PDF to buffer
            pdf.showPage()
            pdf.save()
            pdf_data = buffer.getvalue()
            buffer.close()
            ab.challan_file.save(f'{name}_bank_challan.pdf', ContentFile(pdf_data))
            ab.save()
            #Learner PDF

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="learner_report.pdf"'

            # Create a buffer object to store PDF
            buffer = io.BytesIO()

            # Create the PDF object, using the BytesIO object as its file
            pdf = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)

            # Define styles
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))

            # Define data for the table
            data = [
                ['Full Name: {}'.format(name), 'Son of: {}'.format(fname)],
                ['Gender: {}'.format(gender), 'CNIC NO: {}'.format(cnic)],
                ['Permit No:{}'.format(challan_id), 'Age: {}'.format(age)],
                ['Vehicle Description: Car/Jeep', 'Issue date: {}'.format(today.strftime("%Y-%m-%d"))],
                ['', 'Expiry date: {}'.format(last_date.strftime("%Y-%m-%d"))],
                ['Eligible to appear for Test after {}'.format(elligible.strftime("%Y-%m-%d")), '']
            ]

            # Create the table and add data to it
            table = Table(data, colWidths=[4*inch, 4*inch], rowHeights=[0.5*inch]*6, style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c9daf8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFFFFF')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            # Add the table to the PDF
            pdf_elements = []

            # Add logo to PDF
            logo_path = settings.STATIC_ROOT + '\logo 3.png'
            logo = Image(logo_path, 2*inch, 1*inch)
            pdf_elements.append(logo)

            pdf_elements.append(Spacer(1, 24))
            heading = Paragraph('<strong>Learner Driving Permit</strong>', styles['Center'])
            pdf_elements.append(heading)
            pdf_elements.append(Spacer(1, 24))

            # Add the table to PDF
            pdf_elements.append(table)
            pdf_elements.append(Spacer(1, 24))

            # Add terms and conditions to PDF
            terms = Paragraph('* Is hereby permitted to drive as learner subject to provision of \n Motor Vehicle Rules, 19 of 1969', styles['Normal'])
            pdf_elements.append(terms)

            # Add signature to PDF
            signature_path = settings.STATIC_ROOT + '\sign.png'
            signature = Image(signature_path, 2*inch, 1*inch)
            pdf_elements.append(signature)
            heading = Paragraph('<strong>Motor Licensing Authority</strong>', styles['Center'])
            pdf_elements.append(heading)
            
            # Build PDF
            pdf.build(pdf_elements)

            # Get the value of the BytesIO buffer and write it to the response
            learner_file = buffer.getvalue()
            buffer.close()
            ab.learner_file.save(f'{name}_Learner.pdf', ContentFile(learner_file))
        

            # Store the user's information in the messages framework
            messages.success(request, f"Full Name: {name}, CNIC: {cnic}, DOB: {dob}, Height: {height}, Gender: {gender}, Bloodgroup: {bloodgroup}")

            return redirect('registration')

    else:
        return render(request, 'users/registration.html',{"profile":request.user.profile})

def download_pdf(request):
    user_data = get_object_or_404(userdata, profile__user=request.user)
    if user_data.challan_file:
        response = HttpResponse(user_data.challan_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{user_data.challan_file.name}"'
        return response
    else:
        return HttpResponse('No PDF file found for this user.')

def generate_pdf(request):
    user_data = get_object_or_404(userdata, profile__user=request.user)
    if user_data.learner_file:
        response = HttpResponse(user_data.learner_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{user_data.learner_file.name}"'
        return response
    else:
        return HttpResponse('No PDF file found for this user.')

def contactus(request):
    n=''
    if request.method == 'POST':
        name= request.POST.get('name')
        email= request.POST.get('email')
        subject= request.POST.get('subject')
        message= request.POST.get('message')
        en=contact(Fullname=name,Email=email,Subject=subject,Message=message)
        en.save()
        en.send_email()

        n='Your message was sent, thank you!'
    return render(request, 'users/contactus.html',{'n':n})


class RegisterView(View):
    form_class = RegisterForm
    initial = {'key': 'value'}
    template_name = 'users/register.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(to='/')

        return super(RegisterView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            # Send email verification
            current_site = get_current_site(request)
            mail_subject = 'Activate your account'
            message = render_to_string('users/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': default_token_generator.make_token(user),
            })
            send_mail(
                mail_subject,
                strip_tags(message),
                settings.DEFAULT_FROM_EMAIL,
                [form.cleaned_data.get('email')],
                html_message=message
            )

            messages.success(request, 'Please check your email to activate your account.')
            return redirect('login')

        return render(request, self.template_name, {'form': form})
class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            # set session expiry to 0 seconds. So it will automatically close the session after the browser is closed.
            self.request.session.set_expiry(0)

            # Set session as modified to force data updates/cookie to be saved.
            self.request.session.modified = True
        else:
            # set session expiry to the value of SESSION_COOKIE_AGE defined in settings.py
            self.request.session.set_expiry(60)

            # Store the user's username in local storage
            username = form.cleaned_data.get('username')
            self.request.session['login_username'] = username

            # Store the user's remember me preference in local storage
            self.request.session['login_remember_me'] = remember_me

        return super(CustomLoginView, self).form_valid(form)


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.html'
    success_url = reverse_lazy('users-home')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            messages.error(self.request, "No account found with the provided email.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return "We've emailed you instructions for setting your password, " \
               "if an account exists with the email you entered. You should receive them shortly." \
               " If you don't receive an email, " \
               "please make sure you've entered the address you registered with, and check your spam folder."
    def get_success_url(self):
        return self.request.path
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = messages.get_messages(self.request)
        return context

class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'users/change_password.html'
    success_message = "Successfully Changed Your Password"
    success_url = reverse_lazy('users-home')


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile is updated successfully')
            return redirect(to='users-profile')
    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

    return render(request, 'users/profile.html', {'user_form': user_form, 'profile_form': profile_form})
