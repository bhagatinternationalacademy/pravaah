from django.db import models
from pravaah.trainers.models import Trainer


class Skill(models.Model):
    skill_id = models.AutoField(primary_key=True)
    skill_name = models.CharField(max_length=200)

    def __str__(self):
        return self.skill_name


class TrainerSkill(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency_level = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.trainer} - {self.skill} ({self.proficiency_level})"

