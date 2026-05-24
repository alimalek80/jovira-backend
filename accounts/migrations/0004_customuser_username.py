from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_customuser_agency_customuser_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="username",
            field=models.CharField(blank=True, max_length=150, null=True, unique=True, verbose_name=_("Username")),
        ),
    ]