# Generated by Django 5.1.5 on 2025-03-15 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nagoyameshi', '0002_alter_restaurant_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='capacity',
            field=models.PositiveIntegerField(default=20, verbose_name='収容人数'),
        ),
    ]
