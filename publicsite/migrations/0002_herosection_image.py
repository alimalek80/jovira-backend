from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("publicsite", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="herosection",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="publicsite/hero/", verbose_name="Image"),
        ),
    ]