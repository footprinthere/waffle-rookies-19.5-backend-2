# Generated by Django 3.2.6 on 2021-09-14 12:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_auto_20210913_1405'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='user_seminar_table',
        ),
    ]
