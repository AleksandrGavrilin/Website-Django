import random
import time
from django.shortcuts import render, redirect
from .models import *
from django.db.models import Avg 
from django.http import HttpResponse, HttpResponseServerError
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from .forms import *


#  user logout
def logouttologin(request):
    logout(request)
    return redirect('/login/')


# get category
def get_cat():
    return Category.objects.vealues_list('name', flat=True)


# Saving the user-specified joke rating.
@csrf_exempt
def save_rating(request):
    anek_id = request.POST.get('anek_id', None)
    stars = request.POST.get('stars', None)
    user = request.user
    if anek_id and stars:
        old_stars, _ = Ratings.objects.get_or_create(anek__id=anek_id, user=user)
        old_stars.rating = stars
        old_stars.save()
        messages.success(request, "Ваша оценка анекдота добавлена!")
    else:
        messages.error(request, "Ошибка изменения рейтинга!")
    return redirect("/anek/")


# load rating
def load_rating(anek_id, user_id):
    rating = Ratings.objects.filter(anek__id=anek_id, user__id=user_id).all()
    if len(rating) == 0:
        real_rating = 0
    else:
        real_rating = rating[0].rating
    count_rating = Ratings.objects.filter(anek__id=anek_id).count()
    avg = Ratings.objects.filter(anek__id=anek_id).aggregate(Avg('rating')) ['rating__avg'] 
    avg_rating = round(avg, 2) if avg else 0.0
    return avg_rating, count_rating, real_rating


# main page with jokes
def anek(request): 
    if not request.user.is_authenticated:
        return redirect("/login/")
    user_id = request.user.id
    if request.method == 'GET':
        number_of_jokes = Anek.objects.count()
        l = list(range(1, number_of_jokes+1))
    elif request.method == 'POST':
        cat = int(request.POST.get('category', 1))
        joke_list = Anek.objects.filter(cat = cat)
        number_of_jokes = len(joke_list)
        l = [j.id for j in joke_list]
    random.seed(time.time())
    l2 = random.choices(l, k=5)
    jokes = Anek.objects.filter(id__in = l2)
    cats = Category.objects.all()
    list_category = [(c.name, c.id) for c in cats]
    list_anek = [(j.text, j.id, *load_rating(j.id, user_id)) for j in jokes]
    return render(request, 'anek.html', {'n': number_of_jokes, 
                                         'list_anek': list_anek, 'category': list_category})
    

# user login page
def login_view(request):
    if request.method =='POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd['username'], password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, "Авторизация выполнена успешно!")
                    if user.is_superuser:
                        return redirect("/admin/")
                    return redirect("/anek/")
                
                else:

                    messages.error(request, 'Отключенная учетная запись!')
            else:
                messages.error(request, 'Не правильный логин!')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})       
    

# page that adding a new joke by user
def new(request):
    if not request.user.is_authenticated:
        return redirect("/login/")
    user = request.user
    if request.method =='POST':
        new_form = NewJokeForm(request.POST)
        if new_form.is_valid():
            cd = new_form.cleaned_data
            id_cat = int(cd['category'])
            try:
                cat = Category.objects.get(id = id_cat)
            except:
                messages.error(request, 'Категория не найдена!')
            new_anek_text = cd['new_anek']
            add_anek = NewAnek.objects.create(user=user, cat=cat, text=new_anek_text)
            
            if not add_anek.id:
                return HttpResponseServerError("Ошибка базы данных!")
            messages.success(request, 'Анекдот направлен на рассмотрение администратору!')
            return redirect('/anek/')

            
    else:
        new_form = NewJokeForm()
    return render(request, 'new.html', {'new_form': new_form})


# user registration pagesa
def registration(request):
    if request.method =='POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            cd = user_form.cleaned_data
            if User.objects.filter(username=cd['username']).exists():
                messages.error(request, "Логин уже использован!")
            elif User.objects.filter(email=cd['email']).exists():
                messages.error(request, "Электронная почта уже используется!")
            elif cd['password'] != cd['password2']:
                messages.error(request, "Пароль не подходит")
            else:
                user = User.objects.create_user(cd['username'], cd['email'], cd['password'])
                user.first_name = cd['first_name']
                user.last_name = cd['last_name']
                user.save()
                messages.success(request, 'Пользователь создан!')
                return redirect('/login/')
    else:
        user_form = UserRegistrationForm()
    return render(request, 'registration.html', {'user_form': user_form})


