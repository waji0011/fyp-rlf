# Generated by Django 4.1.2 on 2023-03-12 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_fee_alter_userdata_cnic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fee',
            name='fee',
            field=models.IntegerField(null=True),
        ),
    ]
