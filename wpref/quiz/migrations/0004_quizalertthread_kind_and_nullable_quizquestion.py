from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0003_quizalertthread_quizalertmessage"),
    ]

    operations = [
        migrations.AddField(
            model_name="quizalertthread",
            name="kind",
            field=models.CharField(
                choices=[("question", "Question"), ("assignment", "Assignment")],
                default="question",
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="quizalertthread",
            name="quizquestion",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="alert_threads",
                to="quiz.quizquestion",
            ),
        ),
    ]
