from django.db import migrations, models


def seed_quiz_template_translations(apps, schema_editor):
    QuizTemplate = apps.get_model("quiz", "QuizTemplate")
    for template in QuizTemplate.objects.all().iterator():
      translations = template.translations if isinstance(template.translations, dict) else {}
      if not translations:
        translations = {
          "fr": {
            "title": template.title or "",
            "description": template.description or "",
          }
        }
      template.translations = translations
      template.save(update_fields=["translations"])


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0003_quiztemplate_updated_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="quiztemplate",
            name="translations",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(seed_quiz_template_translations, migrations.RunPython.noop),
    ]
