from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitor", "0004_myimage_metadata_myimage_processed_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="myimage",
            name="feedback_edited_by_user",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="myimage",
            name="top_classification",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
