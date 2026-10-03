from datetime import date

from app.models import Member


def is_eligible(member: Member, service_date: date) -> bool:
    if service_date < member.coverage_start:
        return False
    if member.coverage_end is not None and service_date > member.coverage_end:
        return False
    return True
