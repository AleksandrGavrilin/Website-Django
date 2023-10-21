from django import forms
from .models import Category


class LoginForm(forms.Form):
    username = forms.CharField(label='Логин:')
    password = forms.CharField(widget=forms.PasswordInput, label ='Пароль:')


class UserRegistrationForm(forms.Form):
    username = forms.CharField(label='Логин:', max_length=20, min_length=6, required=True)
    password = forms.CharField(label='Пароль:', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повторите пароль:', widget=forms.PasswordInput)
    email = forms.EmailField(label='Почта:', required=True)
    first_name = forms.CharField(label='Имя:',max_length=30, min_length=1, required=True)
    last_name = forms.CharField(label='Фамилия:',max_length=30, min_length=1, required=False)


Category_choices = Category.objects.values_list('id', 'name')

class NewJokeForm(forms.Form):
    category = forms.ChoiceField(label='Категория:', choices=Category_choices)
    new_anek = forms.CharField(label='Ваш анекдот:', min_length=3, max_length=500, 
                               widget=forms.Textarea(attrs={'name':'body', 'rows':3, 'cols':5}))

