import os

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.staticfiles.views import serve
from django.core.files.storage import FileSystemStorage
from django.db.models.query import prefetch_related_objects
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from rest_framework.generics import get_object_or_404

from api.models import Image, ImageFile
from main.authorization import *

from .forms import AdminEditForm, AdminRegisterForm, LoginForm, RegisterForm
from .models import User


@login_required
def home(request):
    if(is_admin(request.user)):
        images = Image.objects.all().prefetch_related('image_files')
    else:
        images = Image.objects.filter(user_id=request.user.id).prefetch_related('image_files')
    return render(request, 'dashboard.html', {'images':images})

@user_passes_test(is_guest, login_url=dashboard_url)
def login_user(request):
    if request.method == "POST":
        user = authenticate(username = request.POST.get('email'), password = request.POST.get('password'))
        if user is not None:
            if request.POST.get('remember') is not None:    
                request.session.set_expiry(1209600)
            login(request, user)
            return redirect('dashboard')
        else:
            form = LoginForm(request.POST)
            messages.error(request, 'Invalid User Credentials')
            return render(request, 'auth/login.html', {'form':form})
    else:
        if not request.user.is_authenticated:
            if request.GET.get('error') == 'unauthorized':
                messages.error(request, 'Unauthorized Access. Login to Continue.')
            form = LoginForm()
            return render(request, 'auth/login.html', {'form':form})
        else:
            storage = messages.get_messages(request)
            storage.used = True
            if request.GET.get('error') == 'unauthorized':
                messages.error(request, 'Unauthorized Access was denied.')
            return redirect('dashboard')

@user_passes_test(is_guest, login_url=dashboard_url)
def register(request):
    registerForm = RegisterForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if registerForm.is_valid():
            instance = registerForm.save(commit=False)
            instance.set_password(request.POST.get('password1'))
            instance.save()

            storage = messages.get_messages(request)
            storage.used = True
            messages.success(request, 'Registration Success. Login Now.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid Form Request')
    
    if not request.user.is_authenticated:
        return render(request, "auth/register.html", {"form": registerForm})
    else:
        return redirect('dashboard')

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, 'Logged Out Successfully')
    return redirect('login')

@user_passes_test(is_admin, login_url=login_url)
def list_all_users(request):
    users = User.objects.all()
    return render(request, 'users/allusers.html',{'users':users})

# Add Users via Admin Panel Dashboard
@user_passes_test(is_admin, login_url=login_url)
def admin_userAddForm(request, id=0):
    if request.method == "GET":
        if id == 0:
            adminRegisterForm = AdminRegisterForm()
        else:
            edituser = User.objects.get(id=id)
            adminRegisterForm = AdminEditForm(instance=edituser)
        return render(request, "users/admin_register.html", {"form": adminRegisterForm})
    elif request.method == "POST":
        if id == 0:
            form = AdminRegisterForm(request.POST or None, request.FILES or None)

            if form.is_valid():
                form.save()
                messages.success(request, "User Added Successfully!")
            else:
                return render(request, "users/admin_register.html", {"form": form})
        else:
            updateUser = User.objects.get(id=id)
            updateUser.email = request.POST.get('email')
            updateUser.full_name = request.POST.get('full_name')
            updateUser.user_type = request.POST.get('user_type')

            password1 = request.POST.get('password1') 
            password2 = request.POST.get('password2')

            if request.FILES.get('image'):
                updateUser.image.delete()
                myFile = request.FILES.get('image')
                fs = FileSystemStorage(location="mainApp/media/user_images")
                filename = fs.save(myFile.name, myFile)
                updateUser.image = 'user_images/'  + myFile.name
            if password1 and password2:
                if password1 != password2:
                    messages.info(request, "Password Mismatch")
                    return redirect(request.META['HTTP_REFERER'])
                else:
                    updateUser.set_password(password1)
            else:
                if password1 or password2:
                    messages.info(request, "Fill up password in bsoth the fields")
                    return redirect(request.META['HTTP_REFERER'])

            updateUser.save()
            messages.info(request,"User Record Updated Successfully!")

        return redirect("allusers")

# Add Users via Admin Panel Dashboard
@user_passes_test(is_admin, login_url=login_url)
def deleteUserByAdmin(request, id):
    if request.method == "POST":
        user = User.objects.get(id=id)
        user.image.delete()
        user.delete()
        messages.success(request, 'User Record Deleted Successfully!')
        return redirect('allusers')
    else:
        messages.error(request, 'Failed to Delete!')
        return redirect('allusers')
