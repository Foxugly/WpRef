from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customuser", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="nb_domain_max",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
