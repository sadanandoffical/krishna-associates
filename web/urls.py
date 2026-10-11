from django.urls import path

from .views import *


app_name = "web"


urlpatterns = [
    path("", home, name="home"),
    path("associate/login/",associate_login,name="associate-login",),
    path("admin-login/", admin_login, name="admin-login"),
    path("admin-invoices/",admin_invoices,name="admin-invoices",),
    path("admin-invoices/<int:invoice_id>/",admin_invoice_detail,name="admin-invoice-detail",),
    path("admin-invoices/create/",admin_invoice_create,name="admin-invoice-create",),

]