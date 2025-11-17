from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contracts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contractdiffreport",
            name="tool",
            field=models.CharField(
                choices=[
                    ("spectral", "Spectral"),
                    ("openapi-diff", "OpenAPI Diff"),
                    ("oasdiff", "oasdiff"),
                    ("pact-cli", "Pact CLI"),
                ],
                max_length=32,
            ),
        ),
    ]

