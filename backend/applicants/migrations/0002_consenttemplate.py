from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("applicants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConsentTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("version", models.CharField(max_length=30, unique=True)),
                ("title", models.CharField(max_length=180)),
                ("body", models.TextField()),
                ("is_active", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
