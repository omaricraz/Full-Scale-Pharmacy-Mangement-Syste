# Generated by Django 4.2.7 on 2025-06-16 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0020_notification_extra_data_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='extra_data',
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('expiry', 'Product Expiry'), ('low_stock', 'Low Stock'), ('refill', 'Prescription Refill'), ('payment', 'Payment Due'), ('other', 'Other')], max_length=20),
        ),
    ]
