from io import BytesIO
from pathlib import Path

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .models import Invoice


class InvoicePDFError(Exception):
    """Raised when an invoice PDF cannot be generated."""


# Temporary business contact details based on the supplied sample.
# Replace these later with the confirmed Krishna Associates details.
COMPANY_ADDRESS = (
    "Jaunpur, Uttar Pradesh"
)
COMPANY_EMAIL = "info@sheshindia.com"
COMPANY_PHONE = "7068904433"


def _format_amount(amount):
    if amount is None:
        return ""

    return f"₹ {amount:,.2f}"


def _safe_text(value):
    if value is None:
        return ""

    return str(value).replace("&", "&amp;").replace(
        "<", "&lt;"
    ).replace(">", "&gt;")


def _paragraph_text(value):
    return _safe_text(value).replace("\n", "<br/>")


def _format_date(value):
    if not value:
        return ""

    return value.strftime("%d-%m-%Y")


def _field_row(label, value, label_style, value_style):
    if value in (None, ""):
        return None

    return [
        Paragraph(
            f"<b>{_safe_text(label)}</b>",
            label_style,
        ),
        Paragraph(
            _paragraph_text(value),
            value_style,
        ),
    ]


def _build_field_table(
    rows,
    label_style,
    value_style,
    col_widths=(48 * mm, 122 * mm),
):
    rows = [
        row
        for row in rows
        if row is not None
    ]

    if not rows:
        return None

    table = Table(
        rows,
        colWidths=list(col_widths),
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#B8B8B8"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.HexColor("#D8D8D8"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


def render_invoice_pdf(invoice: Invoice) -> bytes:
    """
    Render one persisted Invoice into a deterministic payment receipt PDF.

    This function intentionally contains PDF presentation logic only.
    It does not create, update, or otherwise mutate the Invoice.
    """

    if not invoice.pk:
        raise InvoicePDFError(
            "Invoice must be saved before generating a PDF."
        )

    if not invoice.invoice_number:
        raise InvoicePDFError(
            "Invoice does not have an invoice number."
        )

    try:
        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=16 * mm,
            leftMargin=16 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
            title=f"Payment Receipt {invoice.invoice_number}",
            author="Krishna Associates",
        )

        styles = getSampleStyleSheet()

        company_style = ParagraphStyle(
            "ReceiptCompany",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=20,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#174A35"),
        )

        receipt_title_style = ParagraphStyle(
            "ReceiptTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#174A35"),
            spaceAfter=5 * mm,
        )

        section_style = ParagraphStyle(
            "ReceiptSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=colors.HexColor("#174A35"),
            spaceBefore=3 * mm,
            spaceAfter=2 * mm,
        )

        label_style = ParagraphStyle(
            "ReceiptLabel",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.8,
            leading=11,
        )

        value_style = ParagraphStyle(
            "ReceiptValue",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
        )

        right_value_style = ParagraphStyle(
            "ReceiptRightValue",
            parent=value_style,
            alignment=TA_RIGHT,
        )

        amount_value_style = ParagraphStyle(
            "ReceiptAmount",
            parent=value_style,
            fontName="Helvetica-Bold",
            fontSize=11,
            alignment=TA_RIGHT,
        )

        footer_style = ParagraphStyle(
            "ReceiptFooter",
            parent=value_style,
            fontSize=7.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#666666"),
        )

        note_style = ParagraphStyle(
            "ReceiptNote",
            parent=value_style,
            fontSize=8,
            leading=11,
        )

        story = []

        # ---------------------------------------------------------
        # Header
        # ---------------------------------------------------------

        logo_path = (
            Path(settings.BASE_DIR)
            / "web"
            / "static"
            / "web"
            / "images"
            / "krishna-associates-logo.jpg"
        )

        header_left = []

        if logo_path.exists():
            logo = Image(
                str(logo_path),
                width=45 * mm,
                height=15 * mm,
                kind="proportional",
            )
            header_left.append(logo)

        header_left.append(
            Paragraph(
                "KRISHNA ASSOCIATES",
                company_style,
            )
        )

        header_right = [
            Paragraph(
                "<b>PAYMENT RECEIPT</b>",
                ParagraphStyle(
                    "HeaderReceiptTitle",
                    parent=receipt_title_style,
                    fontSize=13,
                    leading=16,
                    alignment=TA_RIGHT,
                    spaceAfter=0,
                ),
            ),
            Paragraph(
                "Property / Plot Sales",
                ParagraphStyle(
                    "HeaderSubtitle",
                    parent=value_style,
                    alignment=TA_RIGHT,
                    fontSize=8,
                    textColor=colors.HexColor("#666666"),
                ),
            ),
        ]

        header_table = Table(
            [
                [
                    header_left,
                    header_right,
                ]
            ],
            colWidths=[
                105 * mm,
                65 * mm,
            ],
        )

        header_table.setStyle(
            TableStyle(
                [
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (1, 0),
                        (1, 0),
                        "RIGHT",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                ]
            )
        )

        story.append(header_table)

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

        story.append(
            Table(
                [[""]],
                colWidths=[170 * mm],
                rowHeights=[1.2 * mm],
                style=TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            colors.HexColor("#C8A951"),
                        ),
                    ]
                ),
            )
        )

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

        # ---------------------------------------------------------
        # Receipt metadata
        # ---------------------------------------------------------

        metadata = Table(
            [
                [
                    Paragraph(
                        "<b>Receipt No.</b>",
                        label_style,
                    ),
                    Paragraph(
                        _safe_text(invoice.invoice_number),
                        right_value_style,
                    ),
                    Paragraph(
                        "<b>Receipt Date</b>",
                        label_style,
                    ),
                    Paragraph(
                        _format_date(invoice.invoice_date),
                        right_value_style,
                    ),
                ],
            ],
            colWidths=[
                28 * mm,
                57 * mm,
                30 * mm,
                55 * mm,
            ],
        )

        metadata.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        colors.HexColor("#B8B8B8"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(metadata)

        # ---------------------------------------------------------
        # Property details
        # ---------------------------------------------------------

        story.append(
            Paragraph(
                "PROPERTY DETAILS",
                section_style,
            )
        )

        property_rows = [
            _field_row(
                "Project",
                invoice.project,
                label_style,
                value_style,
            ),
            _field_row(
                "Area",
                invoice.plot_area,
                label_style,
                value_style,
            ),
            _field_row(
                "Plot Rate",
                _format_amount(invoice.plot_rate),
                label_style,
                value_style,
            ),
            _field_row(
                "Plot Cost",
                _format_amount(invoice.plot_cost),
                label_style,
                value_style,
            ),
        ]

        property_table = _build_field_table(
            property_rows,
            label_style,
            value_style,
        )

        if property_table:
            story.append(property_table)

        # ---------------------------------------------------------
        # Customer details
        # ---------------------------------------------------------

        story.append(
            Paragraph(
                "CUSTOMER DETAILS",
                section_style,
            )
        )

        customer_id = getattr(
            invoice.customer,
            "id",
            None,
        ) if invoice.customer else None

        customer_rows = [
            _field_row(
                "Customer Name",
                invoice.payee_name,
                label_style,
                value_style,
            ),
            _field_row(
                "Customer ID",
                customer_id,
                label_style,
                value_style,
            ),
            _field_row(
                "Address",
                invoice.payee_address,
                label_style,
                value_style,
            ),
        ]

        customer_table = _build_field_table(
            customer_rows,
            label_style,
            value_style,
        )

        if customer_table:
            story.append(customer_table)

        # ---------------------------------------------------------
        # Payment details
        # ---------------------------------------------------------

        story.append(
            Paragraph(
                "PAYMENT DETAILS",
                section_style,
            )
        )

        payment_rows = [
            _field_row(
                "Paid Amount",
                _format_amount(invoice.paid_amount),
                label_style,
                amount_value_style,
            ),
            _field_row(
                "Due Amount",
                _format_amount(invoice.due_amount),
                label_style,
                value_style,
            ),
            _field_row(
                "Payment As",
                invoice.payment_type,
                label_style,
                value_style,
            ),
            _field_row(
                "Total Paid",
                _format_amount(invoice.total_paid),
                label_style,
                value_style,
            ),
            _field_row(
                "Pay Mode",
                invoice.payment_mode,
                label_style,
                value_style,
            ),
            _field_row(
                "Trans. ID",
                invoice.transaction_id,
                label_style,
                value_style,
            ),
            _field_row(
                "Bank Name",
                invoice.bank_name,
                label_style,
                value_style,
            ),
        ]

        payment_table = _build_field_table(
            payment_rows,
            label_style,
            value_style,
        )

        if payment_table:
            story.append(payment_table)

        # ---------------------------------------------------------
        # Amount in words
        # ---------------------------------------------------------

        if invoice.amount_in_words:
            story.append(
                Spacer(
                    1,
                    3 * mm,
                )
            )

            words_table = Table(
                [
                    [
                        Paragraph(
                            "<b>In Words</b>",
                            label_style,
                        ),
                        Paragraph(
                            _paragraph_text(
                                invoice.amount_in_words
                            ),
                            value_style,
                        ),
                    ]
                ],
                colWidths=[
                    48 * mm,
                    122 * mm,
                ],
            )

            words_table.setStyle(
                TableStyle(
                    [
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.6,
                            colors.HexColor("#B8B8B8"),
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP",
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                    ]
                )
            )

            story.append(words_table)

        # ---------------------------------------------------------
        # Note
        # ---------------------------------------------------------

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

        # note_text = (
        #     "<b>Note:</b><br/>"
        #     "All disputes are subject to Lucknow jurisdiction only."
        # )

        # story.append(
        #     Paragraph(
        #         note_text,
        #         note_style,
        #     )
        # )

        # ---------------------------------------------------------
        # Footer
        # ---------------------------------------------------------

        story.append(
            Spacer(
                1,
                8 * mm,
            )
        )

        footer_rows = [
            # [
            #     Paragraph(
            #         f"<b>Head Office:</b> "
            #         f"{_safe_text(COMPANY_ADDRESS)}",
            #         footer_style,
            #     )
            # ],
            [
                Paragraph(
                    f"<b>Email:</b> "
                    f"{_safe_text(COMPANY_EMAIL)}",
                    footer_style,
                )
            ],
        ]

        if COMPANY_PHONE:
            footer_rows.append(
                [
                    Paragraph(
                        f"<b>Phone:</b> "
                        f"{_safe_text(COMPANY_PHONE)}",
                        footer_style,
                    )
                ]
            )

        footer_table = Table(
            footer_rows,
            colWidths=[170 * mm],
        )

        footer_table.setStyle(
            TableStyle(
                [
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                ]
            )
        )

        story.append(footer_table)

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

        story.append(
            Paragraph(
                "This is a computer-generated payment receipt.",
                footer_style,
            )
        )

        document.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        if not pdf_bytes:
            raise InvoicePDFError(
                "PDF generation returned an empty document."
            )

        return pdf_bytes

    except InvoicePDFError:
        raise

    except Exception as exc:
        raise InvoicePDFError(
            "Unable to generate invoice PDF."
        ) from exc