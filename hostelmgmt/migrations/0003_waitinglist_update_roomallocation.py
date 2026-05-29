from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hostelmgmt', '0002_alter_maintenancerequest_requested_by_and_more'),
    ]

    operations = [
        # Add new fields to RoomAllocation
        migrations.AddField(
            model_name='roomallocation',
            name='person_type',
            field=models.CharField(
                choices=[('student', 'Student'), ('trainer', 'Trainer')],
                default='student', max_length=10
            ),
        ),
        migrations.AddField(
            model_name='roomallocation',
            name='checkin_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='roomallocation',
            name='checkout_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='roomtransfer',
            name='student_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        # Create WaitingList table
        migrations.CreateModel(
            name='WaitingList',
            fields=[
                ('waiting_id', models.AutoField(primary_key=True, serialize=False)),
                ('person_type', models.CharField(
                    choices=[('student', 'Student'), ('trainer', 'Trainer')],
                    default='student', max_length=10
                )),
                ('person_id', models.CharField(max_length=50)),
                ('person_name', models.CharField(max_length=100)),
                ('gender', models.CharField(
                    choices=[('male', 'Male'), ('female', 'Female')], max_length=10
                )),
                ('checkin_date', models.DateField(blank=True, null=True)),
                ('checkout_date', models.DateField(blank=True, null=True)),
                ('added_on', models.DateField(auto_now_add=True)),
                ('status', models.CharField(
                    choices=[('waiting', 'Waiting'), ('allocated', 'Allocated'), ('cancelled', 'Cancelled')],
                    default='waiting', max_length=20
                )),
            ],
            options={'db_table': 'waiting_list'},
        ),
    ]