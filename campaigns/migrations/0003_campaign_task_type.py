# Generated by Django 5.1.7 on 2025-04-03 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0002_campaign_reward_amount_campaign_reward_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='task_type',
            field=models.CharField(choices=[('referral', 'Referral'), ('feedback', 'Feedback Request'), ('survey', 'Survey'), ('testimonial', 'Testimonial Request')], default='referral', max_length=20),
        ),
    ]
