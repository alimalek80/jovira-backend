from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("publicsite", "0002_herosection_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="herosection",
            name="logo",
            field=models.ImageField(blank=True, null=True, upload_to="publicsite/logo/", verbose_name="Logo"),
        ),
    ]
