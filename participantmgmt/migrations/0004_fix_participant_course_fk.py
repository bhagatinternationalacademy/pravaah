from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('participantmgmt', '0003_alter_participant_academic_year_id_type'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE participants MODIFY course_id BIGINT NULL; '
                'ALTER TABLE participants ADD CONSTRAINT participants_ibfk_1 '
                'FOREIGN KEY (course_id) REFERENCES courses_tcm (course_id) '
                'ON DELETE SET NULL;'
            ),
            reverse_sql=(
                'ALTER TABLE participants MODIFY course_id INT NULL; '
                'ALTER TABLE participants ADD CONSTRAINT participants_ibfk_1 '
                'FOREIGN KEY (course_id) REFERENCES courses (course_id) '
                'ON DELETE SET NULL;'
            ),
        ),
    ]