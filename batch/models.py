from django.db import models

class Batch(models.Model):
    batch_id = models.AutoField(primary_key=True)
    batch_code = models.CharField(max_length=100)
    batch_name = models.CharField(max_length=100)

    start_date = models.DateField()
    end_date = models.DateField()

    trainer_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'batches'


class BatchAssignment(models.Model):
    """Unmanaged model mapping to existing batch_batchassignment table used elsewhere in the code and migrations.
    Fields are minimal and marked unmanaged so migrations won't attempt to create/drop the table.
    """
    id = models.BigAutoField(primary_key=True)
    batch_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    trainer_id = models.IntegerField(db_column='trainer_id')

    # Optional additional fields present in DB (nullable)
    accepted_date = models.DateTimeField(null=True, blank=True)
    assigned_date = models.DateTimeField(null=True, blank=True)
    course_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    student_count = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'batch_batchassignment'