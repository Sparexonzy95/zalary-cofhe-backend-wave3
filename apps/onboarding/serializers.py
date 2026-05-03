from __future__ import annotations

from apps.onboarding.models import EmployeeProfile, EmployerProfile, UserProfile


def profile_payload(user: UserProfile) -> dict:
    employer = getattr(user, "employer_profile", None)
    employee = getattr(user, "employee_profile", None)

    return {
        "id": user.id,
        "wallet_address": user.wallet_address,
        "email": user.email,
        "email_verified": user.email_verified,
        "last_selected_role": user.last_selected_role,
        "employer": {
            "company_name": employer.company_name if employer else "",
            "work_email": employer.work_email if employer else "",
            "company_size": employer.company_size if employer else "",
            "onboarding_completed": employer.onboarding_completed if employer else False,
            "completed_at": employer.completed_at.isoformat() if employer and employer.completed_at else None,
        },
        "employee": {
            "display_name": employee.display_name if employee else "",
            "notification_email": employee.notification_email if employee else "",
            "private_access_enabled": employee.private_access_enabled if employee else False,
            "onboarding_completed": employee.onboarding_completed if employee else False,
            "completed_at": employee.completed_at.isoformat() if employee and employee.completed_at else None,
        },
    }


def refresh_completion(user: UserProfile) -> None:
    employer = getattr(user, "employer_profile", None)
    employee = getattr(user, "employee_profile", None)

    if employer:
        employer.recompute_completion()
    if employee:
        employee.recompute_completion()
