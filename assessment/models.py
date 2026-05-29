from django.db import models
from pravaah.batch.models import BatchAssignment


class Assessment(models.Model):

    ASSESSMENT_TYPES = [
        ('Assignment', 'Assignment'),
        ('Quiz', 'Quiz'),
        ('Test', 'Test'),
        ('Practical', 'Practical'),
    ]

    batch = models.ForeignKey(
        BatchAssignment,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    assessment_name = models.CharField(max_length=100)

    assessment_type = models.CharField(
        max_length=20,
        choices=ASSESSMENT_TYPES
    )

    due_date = models.DateField()

    total_marks = models.IntegerField()

    description = models.TextField()

    def __str__(self):
        return self.assessment_name
