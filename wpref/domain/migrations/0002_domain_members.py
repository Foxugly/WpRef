from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("domain", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="domain",
            name="members",
            field=models.ManyToManyField(
                blank=True,
                related_name="linked_domains",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
