from django.shortcuts import render


def home(request):
    return render(request, "web/home.html")

def associate_login(request):
    return render(request, "web/associate_login.html")

def admin_login(request):
    return render(request, "web/admin_login.html")

def admin_invoices(request):
    return render(request, "web/admin_invoices.html")

def admin_invoice_detail(request, invoice_id):
    return render(
        request,
        "web/admin_invoice_detail.html",
        {
            "invoice_id": invoice_id,
        },
    )

def admin_invoice_create(request):
    return render(
        request,
        "web/admin_invoice_create.html",
    )