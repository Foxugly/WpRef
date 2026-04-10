from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("domain", "0003_domain_updated_by"),
    ]

    operations = [
        migrations.RenameField(
            model_name="domain",
            old_name="staff",
            new_name="managers",
        ),
    ]
