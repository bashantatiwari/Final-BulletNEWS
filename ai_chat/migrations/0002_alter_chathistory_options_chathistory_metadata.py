# Generated by Django 5.2.1 on 2025-05-18 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_chat', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chathistory',
            options={'ordering': ['-created_at'], 'verbose_name_plural': 'Chat histories'},
        ),
        migrations.AddField(
            model_name='chathistory',
            name='metadata',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
