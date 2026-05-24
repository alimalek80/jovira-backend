from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='HeroSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('badge_text', models.CharField(default='Discover your next journey', max_length=120, verbose_name='Badge Text')),
                ('headline', models.CharField(default='Find Premium Hotels and Curated Tour Experiences in Minutes', max_length=255, verbose_name='Headline')),
                ('description', models.TextField(default='Jovira helps travelers and agencies discover top-rated stays, unforgettable tours, and smooth travel services across Turkey.', verbose_name='Description')),
                ('search_placeholder', models.CharField(default='Search hotels by location or name', max_length=255, verbose_name='Search Placeholder')),
                ('search_button_text', models.CharField(default='Search Now', max_length=80, verbose_name='Search Button Text')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Hero Section',
                'verbose_name_plural': 'Hero Section',
            },
        ),
    ]
