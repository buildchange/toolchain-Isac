# Generated by Django 3.0.2 on 2020-02-17 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_auto_20200122_1603'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagefile',
            name='tested',
            field=models.BooleanField(default=False),
        ),
    ]