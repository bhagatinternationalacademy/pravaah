from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('trainers', '0004_rename_join_date_to_joining_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('participant_id', models.IntegerField()),
                ('batch_id', models.IntegerField(blank=True, null=True)),
                ('session_date', models.DateField()),
                ('status', models.CharField(choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Late', 'Late')], max_length=10)),
                ('marked_at', models.DateTimeField(auto_now_add=True)),
                ('marked_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'attendance',
                'ordering': ['-session_date'],
            },
        ),
    ]
