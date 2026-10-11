import secrets
import string

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import AssociateProfile


User = get_user_model()


def generate_associate_id():
    """
    Generate a unique Associate ID.

    Current format:
        KA-XXXXXXXX

    The exact business format is not defined by the product
    specification, so this is an implementation assumption.
    """

    alphabet = string.ascii_uppercase + string.digits

    while True:
        suffix = "".join(
            secrets.choice(alphabet)
            for _ in range(8)
        )

        associate_id = f"KA-{suffix}"

        if not AssociateProfile.objects.filter(
            associate_id=associate_id
        ).exists():
            return associate_id


def generate_temporary_password(length=12):
    """
    Generate a strong temporary password.

    The plaintext value is returned to the caller only.
    It is never stored directly in the database.
    """

    alphabet = (
        string.ascii_letters
        + string.digits
        + "!@#$%^&*"
    )

    return "".join(
        secrets.choice(alphabet)
        for _ in range(length)
    )


@transaction.atomic
def create_associate(
    *,
    name,
    email="",
    phone="",
    picture=None,
):
    """
    Create an Associate User + AssociateProfile.

    Returns:
        profile, temporary_password

    The temporary password must be treated as a one-time
    credential reveal by the caller.
    """

    associate_id = generate_associate_id()
    temporary_password = generate_temporary_password()

    username = associate_id

    user = User(
        username=username,
        email=email or "",
        role=User.ROLE_ASSOCIATE,
        is_staff=False,
        is_superuser=False,
        is_active=True,
    )

    user.set_password(temporary_password)
    user.save()

    profile = AssociateProfile.objects.create(
        user=user,
        associate_id=associate_id,
        name=name,
        email=email or "",
        phone=phone or "",
        picture=picture,
    )

    return profile, temporary_password


@transaction.atomic
def reset_associate_password(profile):
    """
    Generate and set a new temporary password for an Associate.

    Returns:
        temporary_password

    The plaintext password is returned only to the caller.
    It is never stored directly in the database.
    """

    temporary_password = generate_temporary_password()

    user = profile.user
    user.set_password(temporary_password)
    user.save(
        update_fields=["password"]
    )

    return temporary_password