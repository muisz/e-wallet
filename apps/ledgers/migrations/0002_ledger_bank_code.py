# Generated by Django 4.2.7 on 2023-11-18 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ledgers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ledger',
            name='bank_code',
            field=models.CharField(default=None, max_length=20),
            preserve_default=False,
        ),
    ]
