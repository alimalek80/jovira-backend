from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_customuser_username"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customuser",
            name="username",
        ),
    ]
