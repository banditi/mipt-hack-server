import random

from django import forms
from django.core import validators
from django.contrib.auth.forms import SetPasswordForm
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import datetime
from django.core.mail import send_mail

from joinme.models import *


class RegistrationForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        max_length=40,
        required=True,
        )
    password = forms.CharField(
        label=_("Password"),
        max_length=60,
        required=True,
        widget=forms.PasswordInput()
        )

    @staticmethod
    def is_valid_username(field_data):
        try:
            User.objects.get(username=field_data)
        except User.DoesNotExist:
            return
        return validators.ValidationError("The username '%s' is already taken." % field_data)

    @staticmethod
    def save(new_data):
        u = User.objects.create_user(
            new_data["email"],
            new_data["email"],
            new_data["password"],
            last_login=datetime.now()
            )
        u.is_active = False
        u.save()
        return u


class EditUser(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'email': forms.EmailInput(attrs={"readonly": ""})
        }


class EditUserProfile(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ('user',)


class ResetForm(SetPasswordForm):
    pass


class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"), 
        max_length=254
        )

    def is_valid_email(self, data):
        try:
            return User.objects.get(username=data)
        except User.DoesNotExist:
            self.add_error("email", "User with email %s does not exist. " % data)
            return None

    @staticmethod
    def generate_password():
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        upperalphabet = alphabet.upper()
        pw_len = 8
        pwlist = []

        for i in range(pw_len//3):
            pwlist.append(alphabet[random.randrange(len(alphabet))])
            pwlist.append(upperalphabet[random.randrange(len(upperalphabet))])
            pwlist.append(str(random.randrange(10)))
        for i in range(pw_len-len(pwlist)):
            pwlist.append(alphabet[random.randrange(len(alphabet))])

        random.shuffle(pwlist)
        return "".join(pwlist)

    def send_password(self, data):
        new_pass = self.generate_password()
        curr_user = User.objects.get(username__exact=data)
        curr_user.set_password(new_pass)
        curr_user.save()
        email_subject = "Reset password"
        email_body = "Hello, %s, and you reset password for an \
master-igor.com account!\n\nYour new password: %s \n\n\
After sign in, please, change you password in Settings page of your account:\n\
\thttp://master-igor.com/%s" % (
            curr_user.username,
            new_pass,
            reverse("joinme:settings")
            )
        return send_mail(
            email_subject,
            email_body,
            "noreply@master-igor.com",
            [curr_user.email]
            )


class CreateEventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = ('title', 'description', 'category', 'datetime', 'active')
        labels = {
            'datetime': 'Date of Event',
            'active': 'Publish an Event? (After publish you cannot change this field)',
        }
        help_text = {
        }
        error_message = {
        }
        widgets = {
            'category': forms.RadioSelect(),
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class EditEventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = ('title', 'description', 'category', 'datetime', 'active')
        labels = {
            'datetime': 'Date of Event',
            'active': 'Publish an Event? (After publish you cannot change this field)',
        }
        widgets = {
            'category': forms.RadioSelect(),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super(EditEventForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.active:
            self.fields['active'].widget.attrs['disabled'] = True
        kwargs['current'] = instance.category.title

    def clean_active(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.active:
            return instance.active
        return self.cleaned_data['active']
