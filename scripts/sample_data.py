import os
import sys
from datetime import date, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pravaah.settings')
import django
django.setup()

from trainers.models import Trainer
from skills.models import Skill, TrainerSkill
from certifications.models import Certification
from django.contrib.auth import get_user_model

User = get_user_model()

# realistic skills
skill_names = ['Python','Data Science','AI','Java','Web Development','SQL','Machine Learning','Django']
skills = []
for name in skill_names:
    s, _ = Skill.objects.get_or_create(skill_name=name)
    skills.append(s)

# realistic trainer names
names = [
    ('Rahul','Sharma'),
    ('Priya','Singh'),
    ('Ankit','Verma'),
    ('Sanya','Kapoor'),
    ('Vikram','Patel'),
    ('Aisha','Khan'),
    ('Rohan','Mehta'),
    ('Neha','Gupta'),
    ('Arjun','Rao'),
    ('Meera','Nair'),
    ('Sunita','Joshi'),
    ('Karan','Malhotra'),
    ('Isha','Reddy'),
    ('Dev','Kapoor'),
    ('Tanvi','Desai'),
    ('Sameer','Shah'),
    ('Alok','Jain'),
    ('Kavya','Iyer'),
    ('Prakash','Balan'),
    ('Shreya','Bhattacharya'),
]

import random

for idx, (first, last) in enumerate(names, start=1):
    code = f"TR{idx:03d}"
    qual = random.choice(['BSc','BA','MSc','MBA'])
    spec = random.choice(['Data Science','Web Development','AI','Cloud'])
    mobile = f"9{random.randint(600000000,999999999)}"
    email = f"{first.lower()}.{last.lower()}@example.com"
    joining = date.today() - timedelta(days=30*idx)
    status = random.choice(['Active']*4 + ['Inactive'])
    avail = random.choice(['Available','Busy','On Leave'])

    t, created = Trainer.objects.update_or_create(
        trainer_code=code,
        defaults={
            'first_name': first,
            'last_name': last,
            'qualification': qual,
            'specialization': spec,
            'mobile': mobile,
            'email': email,
            'joining_date': joining,
            'status': status,
            'availability': avail,
        }
    )

    # assign 1-4 random skills
    chosen = random.sample(skills, k=random.randint(1,4))
    for s in chosen:
        TrainerSkill.objects.update_or_create(trainer=t, skill=s, defaults={'proficiency_level': random.choice(['Beginner','Intermediate','Expert'])})

    # create 0-2 certifications
    cert_count = random.randint(0,2)
    for cidx in range(cert_count):
        name = f"{s.skill_name} Certificate {idx}-{cidx+1}"
        org = random.choice(['GlobalCert','SkillBoard','CertifyPro'])
        issue = date.today() - timedelta(days=random.randint(30,800))
        # mix of expired, expiring, active
        r = random.random()
        if r < 0.2:
            expiry = date.today() - timedelta(days=random.randint(1,200))
        elif r < 0.5:
            expiry = date.today() + timedelta(days=random.randint(1,30))
        else:
            expiry = date.today() + timedelta(days=random.randint(60,900))
        Certification.objects.update_or_create(
            trainer=t,
            certification_name=name,
            defaults={'issuing_organization': org, 'issue_date': issue, 'expiry_date': expiry}
        )

print('Sample data creation completed with realistic names.')
