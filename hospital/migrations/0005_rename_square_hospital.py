from django.db import migrations


def rename_square_hospital(apps, schema_editor):
    Hospital_Information = apps.get_model('hospital', 'Hospital_Information')
    Hospital_Information.objects.filter(name='Square Hospital').update(
        name='Belayet Diagnostic Centre'
    )


def reverse_rename(apps, schema_editor):
    Hospital_Information = apps.get_model('hospital', 'Hospital_Information')
    Hospital_Information.objects.filter(name='Belayet Diagnostic Centre').update(
        name='Square Hospital'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('hospital', '0004_alter_user_login_status'),
    ]

    operations = [
        migrations.RunPython(rename_square_hospital, reverse_code=reverse_rename),
    ]
