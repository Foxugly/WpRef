from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("customuser", "0004_customuser_email_confirmed"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customuser",
            name="new_password_asked",
        ),
    ]
