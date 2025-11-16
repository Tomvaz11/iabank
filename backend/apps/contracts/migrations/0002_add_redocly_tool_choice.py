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
                max_length=32,
                choices=[
                    ("spectral", "Spectral"),
                    ("openapi-diff", "OpenAPI Diff"),
                    ("redocly-cli", "Redocly CLI"),
                    ("pact-cli", "Pact CLI"),
                ],
            ),
        ),
    ]

