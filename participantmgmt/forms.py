from django import forms
from django.contrib.auth.models import User

from participantmgmt.models import Participant


COURSE_CHOICES = [
    ('', '-- Select Course --'),
    ('B.Tech CSE', 'B.Tech CSE'),
    ('B.Tech ECE', 'B.Tech ECE'),
    ('B.Tech ME', 'B.Tech ME'),
    ('B.Tech Civil', 'B.Tech Civil'),
    ('BCA', 'BCA'),
    ('MCA', 'MCA'),
    ('MBA', 'MBA'),
    ('B.Sc', 'B.Sc'),
    ('M.Sc', 'M.Sc'),
]

YEAR_CHOICES = [
    ('', '-- Select Year --'),
    ('1st Year', '1st Year'),
    ('2nd Year', '2nd Year'),
    ('3rd Year', '3rd Year'),
    ('4th Year', '4th Year'),
]

GENDER_CHOICES = [
    ('', '-- Select Gender --'),
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]
class PersonalDetailsForm(forms.Form):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    dob = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    mobile = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Full Address'}))
    photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    guardian_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Name'}))
    relationship = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relationship to Participant'}))
    guardian_mobile = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Mobile Number'}))
    guardian_email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Email Address'}))
    guardian_address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Guardian Address'}))


class AcademicDetailsForm(forms.Form):
    academic_year = forms.ChoiceField(choices=YEAR_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))


class CourseSelectionForm(forms.Form):
    course = forms.ChoiceField(choices=COURSE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data


PAYMENT_METHOD_CHOICES = [
    ('upi', 'UPI'),
    ('card', 'Debit / Credit Card'),
    ('netbanking', 'Net Banking'),
    ('cash', 'Cash at Counter'),
]


class PaymentForm(forms.Form):
    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    transaction_id = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transaction / Reference ID'}))
    receipt = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))


class ParticipantProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Participant
        fields = ['mobile', 'gender', 'dob', 'email']
        widgets = {
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
            self.fields['email'].initial = self.instance.email

    def save(self, commit=True):
        participant = super().save(commit=False)
        participant.email = self.cleaned_data['email']
        if commit:
            from django.contrib.auth.models import User

            user = User.objects.filter(id=participant.user_id).first()
            if user:
                user.first_name = self.cleaned_data['first_name']
                user.last_name = self.cleaned_data['last_name']
                user.email = self.cleaned_data['email']
                user.save()
            participant.first_name = self.cleaned_data['first_name']
            participant.last_name = self.cleaned_data['last_name']
            participant.save(using='server')
        return participant