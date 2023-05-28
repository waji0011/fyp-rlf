# Generated by Django 4.1.2 on 2023-04-29 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_alter_challan_user_alter_video_user'),
    ]

    operations = [
        migrations.DeleteModel(
            name='contact',
        ),
        migrations.DeleteModel(
            name='userdata',
        ),
        migrations.RenameField(
            model_name='challan',
            old_name='user',
            new_name='profile',
        ),
        migrations.RenameField(
            model_name='video',
            old_name='user',
            new_name='profile',
        ),
        migrations.AlterField(
            model_name='video',
            name='video',
            field=models.FileField(upload_to='media/videos_uploaded'),
        ),
    ]
