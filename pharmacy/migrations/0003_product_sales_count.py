# Generated by Django 4.2.7 on 2025-05-18 16:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0002_billing_payment_remove_customercredit_customer_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sales_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
