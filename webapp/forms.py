'''
Created on Dec 19, 2012

@author: kpaskov
'''
from wtforms.fields.simple import TextField, PasswordField, SubmitField
from wtforms.form import Form
from wtforms.validators import Required


class LoginForm(Form):
    username = TextField('Username:', [Required(message='Please log in.')])
    password = PasswordField('Password:') 
    login = SubmitField('Login')

