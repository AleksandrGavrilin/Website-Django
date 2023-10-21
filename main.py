import flask_login
from flask import Flask, render_template, request, redirect, flash, make_response
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField, SelectField, TextAreaField
from wtforms.validators import DataRequired, email, Length
import os
import random
import time
from sqlalchemy.orm import sessionmaker
from db_models import *
from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    from UserLogin import UserLogin
    return UserLogin.getUser(id)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Пользователь вышел из аккаунта', 'info')
    return redirect('/')


@login_manager.unauthorized_handler
def unauthorized():
    return render_template('unauthorized.html')


def get_cat():
    with Session() as db:
        cats = db.query(Cat).all()
        return [c.name for c in cats]


def load_rating(anek_id, user_id):
    with Session() as db:
        rating = db.query(Ratings).filter(Ratings.anek_id == anek_id).filter(Ratings.user_id == user_id).first()
        if rating is None:
            real_rating = 0
        else:
            real_rating = rating.rating
        count_rating = db.query(Ratings.rating).filter(Ratings.anek_id == anek_id).count()
        avg = db.query(func.avg(Ratings.rating)).filter(Ratings.anek_id == anek_id).scalar()
        avg_rating = round(avg, 2) if avg else 0.0
    return avg_rating, count_rating, real_rating


# Главная страница с анекдотами:
@app.route('/anek/', methods=['GET', 'POST'])
@login_required
def joke():
    user_id = int(flask_login.current_user.get_id())
    if request.method == 'GET':
        with Session() as db:
            number_of_jokes = db.query(Joke).count()
        l = list(range(1, number_of_jokes+1))
    elif request.method == 'POST':
        with Session() as db:
            cat = int(request.form['category'])
            joke_list = db.query(Joke).filter(Joke.cat == cat).all()
        number_of_jokes = len(joke_list)
        l = [j.id for j in joke_list]
    random.seed(time.time())
    l2 = random.choices(l, k=5)
    with Session() as db:
        jokes = db.query(Joke).filter(Joke.id.in_(l2)).all()
        cats = db.query(Cat).all()
    list_category = [(c.name, c.id) for c in cats]
    list_anek = [(j.text, j.id, load_rating(j.id, user_id)) for j in jokes]
    return render_template('anek.html', n=number_of_jokes, list_anek=list_anek, category=list_category)


# Сохранение установленного пользователем рейтинга анекдота.
@app.route("/save/", methods=["POST"])
@login_required
def save():
    data = dict(request.form)
    anek_id = int(data["anek_id"])
    stars = data["stars"]
    user_id = int(flask_login.current_user.get_id())
    try:
        with Session() as db:
            old_stars = db.query(Ratings).filter(Ratings.anek_id == anek_id).filter(Ratings.user_id == user_id).first()
            if old_stars is None:
                new_stars = Ratings(anek_id=anek_id, user_id=user_id, rating=stars)
                db.add(new_stars)
                db.commit()
            else:
                old_stars.rating = stars
                db.commit()
        return make_response("OK", 200)
    except Exception:
        return make_response('Internal Server Error', 500)


# Страница для отправки на рассмотрение нового анекдота администратору,
# для последующей возможности добавления анекдота в базу данных.
@app.route('/new/', methods=['GET', 'POST'])
@login_required
def new_joke():
    flag = False
    form = NewJokeForm()
    if form.validate_on_submit():
        userid = int(flask_login.current_user.get_id())
        category = form.category.data
        text = form.new_anek.data
        with Session() as db:
            cat_id = db.query(Cat).filter(Cat.name == category).first().id
            new_anek = NewAnek(cat=cat_id, text=text, userid=userid)
            db.add(new_anek)
            db.commit()
        flag = True
    return render_template('new.html', form=form, flag=flag)


# Подтверждение администратором добавления нового анекдота пользователя в базу данных.
@app.route('/allow/<int:x>')
@login_required
def allow(x):
    userid = int(flask_login.current_user.get_id())
    with Session() as db:
        user = db.query(Users).filter(Users.id == userid).first()
    if user:
        is_admin = user.administrator
        if is_admin:
            with Session() as db:
                new_anek = db.query(NewAnek).filter(NewAnek.id == x).first()
                cat = new_anek.cat
                text = new_anek.text
                anek = Joke(text=text, cat=cat)
                db.add(anek)
                db.delete(new_anek)
                db.commit()
            return redirect('/admin/')


# Отказ администратором добавления нового анекдота пользователя в базу данных.
@app.route('/reject/<int:x>')
@login_required
def reject(x):
    userid = int(flask_login.current_user.get_id())
    with Session() as db:
        user = db.query(Users).filter(Users.id == userid).first()
    if user:
        is_admin = user.administrator
        if is_admin:
            with Session() as db:
                new_anek = db.query(NewAnek).filter(NewAnek.id == x).first()
                db.delete(new_anek)
                db.commit()
            return redirect('/admin/')


# Страница администратора, с проверкой доступа.
@app.route('/admin/', methods=['GET', 'POST'])
@login_required
def admin():
    if flask_login.current_user.is_authenticated:
        userid = int(flask_login.current_user.get_id())
        with Session() as db:
            new_anek_list = db.query(NewAnek, Users, Cat).join(Users).join(Cat).all()
            user = db.query(Users).filter(Users.id == userid).first()
        if user:
            is_admin = user.administrator
            if is_admin:
                return render_template('admin.html', new=new_anek_list)
            else:
                flash('Вы не являетесь администратором!')
                return redirect('/anek/')


@app.route('/send/')
def send():
    return render_template('send.html')


# Страница авторизации.
@app.route('/', methods=['GET', 'POST'])
def login():
    from UserLogin import UserLogin
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember_me = form.remember_me.data
        with Session() as db:
            user = db.query(Users).filter(Users.username == username).first()
            if user and check_password_hash(user.password, password):
                userlogin = UserLogin(user)
                login_user(userlogin, remember_me)
                flash('Вход выполнен успешно!')
                return redirect('/anek/')
            flash('Неверный логин или пароль', 'error')
    return render_template('login.html', form=form)


# Страница регистрации.
@app.route('/registration/', methods=['GET', 'POST'])
def registration():
    from UserLogin import UserLogin
    flag = False
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        password_confrim = form.password_confrim.data
        if password != password_confrim:
            flash('Пароли не совпадают!')
            return redirect('/registration/')
        email = form.email.data
        first_name = form.first_name.data
        second_name = form.second_name.data
        with Session() as db:
            check_email = db.query(Users).filter(Users.email == email).first()
            if check_email:
                flag = True
            else:
                user = Users(email=email, username=username, password=generate_password_hash(password),
                             first_name=first_name, second_name=second_name)
                db.add(user)
                db.commit()
                userlogin = UserLogin(user)
                login_user(userlogin)
                flash('Вход выполнен успешно.')
                return redirect('/anek/')
    return render_template('registration.html', flag=flag, form=form)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or "you-will-never-guess"


class LoginForm(FlaskForm):
    username = StringField('Логин:', validators=[DataRequired(), Length(max=20)])
    password = PasswordField('Пароль:', validators=[DataRequired(), Length(min=6, max=20)])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    username = StringField('Ваш логин:', validators=[DataRequired(), Length(max=20)])
    password = PasswordField('Новый пароль:', validators=[DataRequired(), Length(min=6, max=20)])
    password_confrim = PasswordField('Повторите новый пароль:', validators=[DataRequired(), Length(min=6, max=20)])
    email = EmailField('Ваш E-mail:', validators=[DataRequired(),  email(), Length(max=50)])
    first_name = StringField('Ваша имя:', validators=[DataRequired(), Length(max=20)])
    second_name = StringField('Ваша Фамилия:', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Зарегистрироваться!')


app.config.from_object(Config)


Base.metadata.create_all(bind=engine)
Session = sessionmaker(autoflush=False, bind=engine)

l1 = get_cat()


class NewJokeForm(FlaskForm):
    category = SelectField('Категория:', choices=l1)
    new_anek = TextAreaField('Ваш анекдот:', validators=[DataRequired(), Length(max=500)])
    send = SubmitField('Отправить')


if __name__ == '__main__':
    app.run(debug=True)
