# Generated migration for adding receipt_number to RedeemedPoints
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_rename_student_id_to_school_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='redeemedpoints',
            name='receipt_number',
            field=models.CharField(blank=True, max_length=30, unique=True),
        ),
    ]
