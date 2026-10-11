from django.conf import settings
from django.core.mail import send_mail


class EnquiryEmailError(Exception):
    """Raised when an enquiry email cannot be sent."""


def send_enquiry_email(enquiry):
    recipient = settings.ENQUIRY_ADMIN_EMAIL

    if not recipient:
        raise EnquiryEmailError(
            "Enquiry administrator email is not configured."
        )

    subject = (
        f"New website enquiry from {enquiry.name}"
    )

    message = (
        "A new enquiry has been submitted "
        "through the Krishna Associates website.\n\n"
        f"Name: {enquiry.name}\n"
        f"Phone: {enquiry.phone}\n\n"
        "Requirement:\n"
        f"{enquiry.requirement}\n"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception as exc:
        raise EnquiryEmailError(
            "Unable to send enquiry email."
        ) from exc