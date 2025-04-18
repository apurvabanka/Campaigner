# Generated by Django 5.1.7 on 2025-04-03 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0003_campaign_task_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='task_type',
            field=models.CharField(choices=[('referral', 'Referral'), ('quiz', 'Quiz or Trivia'), ('purchase', 'Make a Purchase'), ('event', 'Attend an Event')], default='referral', max_length=20),
        ),
    ]
