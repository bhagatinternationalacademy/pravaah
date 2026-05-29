from django.db import models

class Trainer(models.Model):
    """
    Mapped to existing 'trainers' table in the database to ensure zero data loss.
    """
    trainer_id = models.BigAutoField(primary_key=True)
    trainer_code = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True)
    join_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Active')
    gender = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = 'trainers'
        managed = False  # Keep as False since table already exists and is managed externally

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def hourly_rate(self):
        # Default hourly rate for payment calculation
        return 750.00

    def __str__(self):
        return f"{self.full_name} ({self.trainer_code})"


class TrainerSkill(models.Model):
    """
    Mapped to existing 'trainer_skills' table in the database.
    """
    id = models.AutoField(primary_key=True)
    skill_id = models.IntegerField()
    proficiency_level = models.CharField(max_length=50)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, db_column='trainer_id')

    class Meta:
        db_table = 'trainer_skills'
        managed = False


class TrainerPayment(models.Model):
    """
    New table for tracking trainer accounting transactions and payments.
    """
    payment_id = models.AutoField(primary_key=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.PROTECT, db_column='trainer_id', related_name='payments')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_mode = models.CharField(max_length=50, choices=[
        ('Bank Transfer', 'Bank Transfer'),
        ('UPI', 'UPI'),
        ('Cheque', 'Cheque'),
        ('Cash', 'Cash')
    ], default='Bank Transfer')
    reference_number = models.CharField(max_length=100, unique=True)
    hours_billed = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('Failed', 'Failed')
    ], default='Completed')
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'trainer_payments'
        ordering = ['-payment_date']

    def __str__(self):
        return f"Voucher #{self.payment_id} - {self.trainer.full_name} - {self.amount_paid}"
