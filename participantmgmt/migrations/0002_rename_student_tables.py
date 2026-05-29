from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('participantmgmt', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE students RENAME TO participants;',
                    reverse_sql='ALTER TABLE participants RENAME TO students;',
                ),
                migrations.RunSQL(
                    sql='ALTER TABLE student_guardians RENAME TO participant_guardians;',
                    reverse_sql='ALTER TABLE participant_guardians RENAME TO student_guardians;',
                ),
            ],
            state_operations=[
                migrations.AlterModelTable(
                    name='student',
                    table='participants',
                ),
                migrations.AlterModelTable(
                    name='studentguardian',
                    table='participant_guardians',
                ),
            ],
        ),
    ]
