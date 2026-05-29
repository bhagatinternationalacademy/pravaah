from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('participantmgmt', '0002_rename_student_tables'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE participants DROP FOREIGN KEY participants_ibfk_2; '
                'ALTER TABLE participants MODIFY academic_year_id VARCHAR(50) NULL;'
            ),
            reverse_sql='ALTER TABLE participants MODIFY academic_year_id INT NULL;',
        ),
    ]