from django.db import migrations

def lowercase_emails(apps, schema_editor):
    User = apps.get_model('socialnetworking', 'CustomUser')
    for user in User.objects.all():
        user.email = user.email.lower()
        user.save()

class Migration(migrations.Migration):
    dependencies = [
        ('socialnetworking','0001_initial'),  # Ensure this matches your last migration
    ]

    operations = [
        migrations.RunPython(lowercase_emails),
    ]
