# Generated by Django 2.2 on 2019-05-09 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('RunScheduleApp', '0005_auto_20190508_1223'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingdiary',
            name='date',
            field=models.DateField(default='2018-01-01', verbose_name='Date'),
            preserve_default=False,
        ),
    ]
