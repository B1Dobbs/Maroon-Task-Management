# Generated by Django 3.0.8 on 2020-08-06 02:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0003_remove_project_max_ticket_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='max_ticket_id',
            field=models.IntegerField(default=0),
        ),
    ]