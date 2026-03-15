from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from hospital.models import User, Hospital_Information
from .models import Admin_Information, Clinical_Laboratory_Technician
from doctor.models import Doctor_Information
from hospital_admin.models import hospital_department, specialization

class AdminUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    # create a style for model form
    def __init__(self, *args, **kwargs):
        super(AdminUserCreationForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            

class LabWorkerCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    # create a style for model form
    def __init__(self, *args, **kwargs):
        super(LabWorkerCreationForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

class PharmacistCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    # create a style for model form
    def __init__(self, *args, **kwargs):
        super(PharmacistCreationForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

# class EditLabWorkerForm(forms.ModelForm):
#     class Meta:
#         model = Clinical_Laboratory_Technician
#         fields = ['name', 'age', 'phone_number', 'featured_image']

#     def __init__(self, *args, **kwargs):
#         super(EditLabWorkerForm, self).__init__(*args, **kwargs)

#         for name, field in self.fields.items():
#             field.widget.attrs.update({'class': 'form-control'})



class AddHospitalForm(ModelForm):
    class Meta:
        model = Hospital_Information
        fields = ['name','address','featured_image','phone_number','email','hospital_type']

    def __init__(self, *args, **kwargs):
        super(AddHospitalForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

class EditHospitalForm(forms.ModelForm):
    class Meta:
        model = Hospital_Information
        fields = ['name','address','featured_image','phone_number','email','hospital_type']

    def __init__(self, *args, **kwargs):
        super(EditHospitalForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class EditEmergencyForm(forms.ModelForm):
    class Meta:
        model = Hospital_Information
        fields = ['general_bed_no','available_icu_no','regular_cabin_no','emergency_cabin_no','vip_cabin_no']

    def __init__(self, *args, **kwargs):
        super(EditEmergencyForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

class AddEmergencyForm(ModelForm):
    class Meta:
        model = Hospital_Information
        fields = ['name','general_bed_no','available_icu_no','regular_cabin_no','emergency_cabin_no','vip_cabin_no']

    def __init__(self, *args, **kwargs):
        super(AddEmergencyForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})



class AdminForm(ModelForm):
    class Meta:
        model = Admin_Information
        fields = ['name', 'email', 'phone_number', 'role','featured_image']

    def __init__(self, *args, **kwargs):
         super(AdminForm, self).__init__(*args, **kwargs)

         for name, field in self.fields.items():
             field.widget.attrs.update({'class': 'form-control'})


class DoctorAccountCreationForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(required=False, widget=forms.PasswordInput)
    password2 = forms.CharField(required=False, widget=forms.PasswordInput)

    name = forms.CharField(max_length=200)
    gender = forms.CharField(max_length=200, required=False)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    hospital_name = forms.ModelChoiceField(queryset=Hospital_Information.objects.all())
    additional_hospitals = forms.ModelMultipleChoiceField(
        queryset=Hospital_Information.objects.all(),
        required=False,
        widget=forms.SelectMultiple,
    )
    department = forms.ChoiceField(choices=Doctor_Information.DOCTOR_TYPE, required=False)
    department_name = forms.ModelChoiceField(queryset=hospital_department.objects.all(), required=False)
    specialization = forms.ModelChoiceField(queryset=specialization.objects.all(), required=False)

    email_profile = forms.EmailField(required=False, label='Doctor Email (profile)')
    phone_number = forms.CharField(max_length=200, required=False)
    nid = forms.CharField(max_length=200, required=False)
    dob = forms.CharField(max_length=200, required=False)
    visiting_hour = forms.CharField(max_length=200, required=False)
    consultation_fee = forms.IntegerField(required=False)
    report_fee = forms.IntegerField(required=False)

    featured_image = forms.ImageField(required=False)
    certificate_image = forms.ImageField(required=False)

    institute = forms.CharField(max_length=200, required=False)
    degree = forms.CharField(max_length=200, required=False)
    completion_year = forms.CharField(max_length=200, required=False)
    work_place = forms.CharField(max_length=200, required=False)
    designation = forms.CharField(max_length=200, required=False)
    start_year = forms.CharField(max_length=200, required=False)
    end_year = forms.CharField(max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput,)):
                continue
            css = 'form-control'
            if isinstance(field.widget, (forms.FileInput, forms.ClearableFileInput)):
                css = 'form-control-file'
            field.widget.attrs.update({'class': css})

        self.fields['password1'].help_text = 'Leave blank to auto-generate a password.'
        self.fields['password2'].help_text = 'Leave blank to auto-generate a password.'

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if (p1 or p2) and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned


class DoctorAdminUpdateForm(forms.Form):
    name = forms.CharField(max_length=200)
    gender = forms.CharField(max_length=200, required=False)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    hospital_name = forms.ModelChoiceField(queryset=Hospital_Information.objects.all())
    additional_hospitals = forms.ModelMultipleChoiceField(
        queryset=Hospital_Information.objects.all(),
        required=False,
        widget=forms.SelectMultiple,
    )
    department = forms.ChoiceField(choices=Doctor_Information.DOCTOR_TYPE, required=False)
    department_name = forms.ModelChoiceField(queryset=hospital_department.objects.all(), required=False)
    specialization = forms.ModelChoiceField(queryset=specialization.objects.all(), required=False)

    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=200, required=False)
    nid = forms.CharField(max_length=200, required=False)
    dob = forms.CharField(max_length=200, required=False)
    visiting_hour = forms.CharField(max_length=200, required=False)
    consultation_fee = forms.IntegerField(required=False)
    report_fee = forms.IntegerField(required=False)

    featured_image = forms.ImageField(required=False)
    certificate_image = forms.ImageField(required=False)

    institute = forms.CharField(max_length=200, required=False)
    degree = forms.CharField(max_length=200, required=False)
    completion_year = forms.CharField(max_length=200, required=False)
    work_place = forms.CharField(max_length=200, required=False)
    designation = forms.CharField(max_length=200, required=False)
    start_year = forms.CharField(max_length=200, required=False)
    end_year = forms.CharField(max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'form-control'
            if isinstance(field.widget, (forms.FileInput, forms.ClearableFileInput)):
                css = 'form-control-file'
            field.widget.attrs.update({'class': css})

