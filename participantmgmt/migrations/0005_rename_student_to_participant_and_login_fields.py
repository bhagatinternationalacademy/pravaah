from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('participantmgmt', '0004_fix_participant_course_fk'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RenameModel(
                    old_name='Student',
                    new_name='Participant',
                ),
                migrations.RenameModel(
                    old_name='StudentGuardian',
                    new_name='ParticipantGuardian',
                ),
            ],
        ),
        migrations.AddField(
            model_name='participant',
            name='username',
            field=models.CharField(blank=True, max_length=150, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='participant',
            name='password_hash',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]
