# Generated by Django 4.1.2 on 2023-05-04 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0024_userdata_pdf_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdata',
            name='pdf_file',
            field=models.BinaryField(blank=True),
        ),
    ]
