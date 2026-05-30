from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('trainers', '0005_add_attendance'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='attendance',
            constraint=models.UniqueConstraint(fields=['participant_id', 'session_date'], name='unique_attendance_per_session'),
        ),
    ]
