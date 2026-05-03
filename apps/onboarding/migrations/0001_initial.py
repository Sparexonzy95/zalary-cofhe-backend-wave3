# Generated for Zalary onboarding implementation.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("wallet_address", models.CharField(db_index=True, max_length=42, unique=True)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("email_verified", models.BooleanField(default=False)),
                ("last_selected_role", models.CharField(blank=True, choices=[("employer", "Employer"), ("employee", "Employee")], default="", max_length=16)),
                ("last_login_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="WalletAuthNonce",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("wallet_address", models.CharField(db_index=True, max_length=42, unique=True)),
                ("nonce", models.CharField(max_length=80)),
                ("message", models.TextField()),
                ("expires_at", models.DateTimeField()),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="EmployerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("company_name", models.CharField(blank=True, default="", max_length=180)),
                ("work_email", models.EmailField(blank=True, default="", max_length=254)),
                ("company_size", models.CharField(blank=True, default="", max_length=50)),
                ("onboarding_completed", models.BooleanField(default=False)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="employer_profile", to="onboarding.userprofile")),
            ],
        ),
        migrations.CreateModel(
            name="EmployeeProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(blank=True, default="", max_length=120)),
                ("notification_email", models.EmailField(blank=True, default="", max_length=254)),
                ("private_access_enabled", models.BooleanField(default=False)),
                ("onboarding_completed", models.BooleanField(default=False)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="employee_profile", to="onboarding.userprofile")),
            ],
        ),
        migrations.CreateModel(
            name="EmailVerificationCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254)),
                ("code_hash", models.CharField(max_length=256)),
                ("purpose", models.CharField(choices=[("onboarding", "Onboarding")], default="onboarding", max_length=32)),
                ("expires_at", models.DateTimeField()),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="email_codes", to="onboarding.userprofile")),
            ],
        ),
        migrations.AddIndex(
            model_name="userprofile",
            index=models.Index(fields=["email"], name="onboarding__email_a5ea_idx"),
        ),
        migrations.AddIndex(
            model_name="userprofile",
            index=models.Index(fields=["last_selected_role"], name="onboarding__last_se_3197_idx"),
        ),
    ]
