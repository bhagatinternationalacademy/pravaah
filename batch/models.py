from django.db import models
from pravaah.trainers.models import Trainer

class BatchAssignment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    trainer = models.ForeignKey(
        Trainer,
        on_delete=models.CASCADE,
        related_name='batch_assignments'
    )

    batch_name = models.CharField(max_length=100)
    
    course_name = models.CharField(max_length=100, blank=True, null=True)

    start_date = models.DateField()

    end_date = models.DateField()
    
    student_count = models.PositiveIntegerField(default=0)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    assigned_date = models.DateTimeField(auto_now_add=True)
    
    accepted_date = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.batch_name} - {self.trainer} ({self.status})"
    
    class Meta:
        ordering = ['-assigned_date']
        unique_together = ('trainer', 'batch_name', 'start_date')
