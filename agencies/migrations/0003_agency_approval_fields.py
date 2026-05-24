from django.db import migrations, models
from django.utils import timezone


def approve_existing_agencies(apps, schema_editor):
    Agency = apps.get_model("agencies", "Agency")
    Agency.objects.filter(is_approved=False).update(is_approved=True, approved_at=timezone.now())


def unapprove_existing_agencies(apps, schema_editor):
    Agency = apps.get_model("agencies", "Agency")
    Agency.objects.update(is_approved=False, approved_at=None)


class Migration(migrations.Migration):

    dependencies = [
        ("agencies", "0002_agency_email_agency_icq_agency_mobile_phone_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="agency",
            name="approved_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Approved At"),
        ),
        migrations.AddField(
            model_name="agency",
            name="is_approved",
            field=models.BooleanField(default=False, verbose_name="Is Approved"),
        ),
        migrations.RunPython(approve_existing_agencies, unapprove_existing_agencies),
    ]