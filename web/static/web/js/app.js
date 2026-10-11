"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const menuButton = document.getElementById("mobileMenuButton");
    const drawer = document.getElementById("mobileDrawer");
    const closeButton = document.getElementById("mobileDrawerClose");
    const backdrop = document.getElementById("mobileDrawerBackdrop");

    if (!menuButton || !drawer || !closeButton || !backdrop) {
        return;
    }

    const openDrawer = () => {
        drawer.classList.add("is-open");
        drawer.setAttribute("aria-hidden", "false");

        menuButton.setAttribute("aria-expanded", "true");

        document.body.classList.add("drawer-open");
    };

    const closeDrawer = () => {
        drawer.classList.remove("is-open");
        drawer.setAttribute("aria-hidden", "true");

        menuButton.setAttribute("aria-expanded", "false");

        document.body.classList.remove("drawer-open");
    };

    menuButton.addEventListener("click", openDrawer);
    closeButton.addEventListener("click", closeDrawer);
    backdrop.addEventListener("click", closeDrawer);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeDrawer();
        }
    });

    drawer.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", closeDrawer);
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("adminLoginForm");

    if (!form) {
        return;
    }

    const usernameInput = document.getElementById("adminUsername");
    const passwordInput = document.getElementById("adminPassword");
    const submitButton = document.getElementById("adminLoginSubmit");
    const errorBox = document.getElementById("adminLoginError");

    const getCsrfToken = () => {
        const tokenInput = form.querySelector(
            'input[name="csrfmiddlewaretoken"]'
        );

        return tokenInput ? tokenInput.value : "";
    };

    const clearErrors = () => {
        errorBox.hidden = true;
        errorBox.textContent = "";

        form.querySelectorAll(".form-field__error").forEach(
            (element) => {
                element.textContent = "";
            }
        );

        usernameInput.classList.remove("is-invalid");
        passwordInput.classList.remove("is-invalid");
    };

    const showFieldErrors = (errors) => {
        Object.entries(errors).forEach(([field, messages]) => {
            const errorElement = form.querySelector(
                `[data-error-for="${field}"]`
            );

            const inputElement = form.querySelector(
                `[name="${field}"]`
            );

            if (errorElement) {
                errorElement.textContent = Array.isArray(messages)
                    ? messages.join(" ")
                    : String(messages);
            }

            if (inputElement) {
                inputElement.classList.add("is-invalid");
            }
        });
    };

    const showGeneralError = (message) => {
        errorBox.textContent = message;
        errorBox.hidden = false;
    };

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        clearErrors();

        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!username) {
            showFieldErrors({
                username: ["Username is required."],
            });

            usernameInput.focus();
            return;
        }

        if (!password) {
            showFieldErrors({
                password: ["Password is required."],
            });

            passwordInput.focus();
            return;
        }

        submitButton.disabled = true;
        submitButton.textContent = "Signing in...";

        try {
            const response = await fetch(
                "/api/accounts/login/admin/",
                {
                    method: "POST",

                    credentials: "same-origin",

                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(),
                    },

                    body: JSON.stringify({
                        username,
                        password,
                    }),
                }
            );

            const data = await response.json();

            if (!response.ok) {
                if (
                    data &&
                    data.errors &&
                    typeof data.errors === "object"
                ) {
                    showFieldErrors(data.errors);
                }

                const message =
                    data?.message ||
                    data?.detail ||
                    (
                        typeof data === "string"
                            ? data
                            : "Unable to sign in."
                    );

                showGeneralError(message);

                return;
            }

            window.location.href = "/admin-invoices/";

        } catch (error) {
            showGeneralError(
                "Unable to connect to the server. Please try again."
            );
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Sign In";
        }
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const invoiceList = document.getElementById("invoiceList");

    if (!invoiceList) {
        return;
    }

    const searchInput = document.getElementById("invoiceSearch");
    const statusInput = document.getElementById("invoiceStatus");
    const dateInput = document.getElementById("invoiceDate");
    const clearButton = document.getElementById(
        "invoiceClearFilters"
    );

    const loadingState = document.getElementById(
        "invoiceLoading"
    );

    const emptyState = document.getElementById(
        "invoiceEmpty"
    );

    const errorState = document.getElementById(
        "invoiceError"
    );

    const pagination = document.getElementById(
        "invoicePagination"
    );

    let currentPage = 1;


    const formatAmount = (amount) => {
        const numericAmount = Number(amount);

        if (Number.isNaN(numericAmount)) {
            return amount;
        }

        return new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: "INR",
            minimumFractionDigits: 2,
        }).format(numericAmount);
    };


    const formatDate = (dateValue) => {
        if (!dateValue) {
            return "—";
        }

        const date = new Date(`${dateValue}T00:00:00`);

        if (Number.isNaN(date.getTime())) {
            return dateValue;
        }

        return new Intl.DateTimeFormat("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
        }).format(date);
    };


    const escapeHtml = (value) => {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    };


    const showError = (message) => {
        errorState.textContent = message;
        errorState.hidden = false;
    };


    const clearError = () => {
        errorState.hidden = true;
        errorState.textContent = "";
    };


    const renderInvoices = (invoices) => {
        invoiceList.innerHTML = "";

        invoices.forEach((invoice) => {
            const card = document.createElement("article");

            card.className = "invoice-card";

            const customerName =
                invoice.customer_name ||
                "Manual invoice";

            card.innerHTML = `
                <div class="invoice-card__top">

                    <div>
                        <h2 class="invoice-card__number">
                            ${escapeHtml(invoice.invoice_number)}
                        </h2>

                        <p class="invoice-card__customer">
                            ${escapeHtml(customerName)}
                        </p>
                    </div>

                    <span
                        class="status-badge status-badge--${escapeHtml(invoice.status)}"
                    >
                        ${escapeHtml(invoice.status)}
                    </span>

                </div>


                <div class="invoice-card__details">

                    <div class="invoice-card__detail">
                        <span class="invoice-card__detail-label">
                            Amount
                        </span>

                        <span class="invoice-card__detail-value">
                            ${escapeHtml(formatAmount(invoice.paid_amount))}
                        </span>
                    </div>


                    <div class="invoice-card__detail">
                        <span class="invoice-card__detail-label">
                            Invoice Date
                        </span>

                        <span class="invoice-card__detail-value">
                            ${escapeHtml(formatDate(invoice.invoice_date))}
                        </span>
                    </div>


                    <div class="invoice-card__detail">
                        <span class="invoice-card__detail-label">
                            Phone
                        </span>

                        <span class="invoice-card__detail-value">
                            ${escapeHtml(invoice.customer_phone || "—")}
                        </span>
                    </div>


                    <div class="invoice-card__detail">
                        <span class="invoice-card__detail-label">
                            Payee
                        </span>

                        <span class="invoice-card__detail-value">
                            ${escapeHtml(invoice.payee_name)}
                        </span>
                    </div>

                </div>


                <div class="invoice-card__actions">

                    <a
                        href="/admin-invoices/${invoice.id}/"
                        class="button button--secondary invoice-card__view"
                    >
                        View Invoice
                    </a>

                </div>
            `;

            invoiceList.appendChild(card);
        });
    };


    const renderPagination = (data) => {
        pagination.innerHTML = "";

        if (!data.count || data.count <= 12) {
            pagination.hidden = true;
            return;
        }

        pagination.hidden = false;

        const previousButton = document.createElement(
            "button"
        );

        previousButton.type = "button";
        previousButton.textContent = "Previous";
        previousButton.disabled = !data.previous;


        previousButton.addEventListener("click", () => {
            if (currentPage > 1) {
                currentPage -= 1;
                loadInvoices();
            }
        });


        const nextButton = document.createElement(
            "button"
        );

        nextButton.type = "button";
        nextButton.textContent = "Next";
        nextButton.disabled = !data.next;


        nextButton.addEventListener("click", () => {
            if (data.next) {
                currentPage += 1;
                loadInvoices();
            }
        });


        const info = document.createElement("span");

        info.className = "invoice-pagination__info";

        const pageCount = Math.ceil(
            data.count / 12
        );

        info.textContent =
            `Page ${currentPage} of ${pageCount}`;


        pagination.appendChild(previousButton);
        pagination.appendChild(info);
        pagination.appendChild(nextButton);
    };


    const loadInvoices = async () => {
        clearError();

        loadingState.hidden = false;
        emptyState.hidden = true;
        invoiceList.innerHTML = "";
        pagination.hidden = true;

        const params = new URLSearchParams();

        params.set("page", String(currentPage));

        const search = searchInput.value.trim();

        if (search) {
            params.set("search", search);
        }

        const status = statusInput.value;

        if (status) {
            params.set("status", status);
        }

        const date = dateInput.value;

        if (date) {
            params.set("created_at", date);
        }


        try {
            const response = await fetch(
                `/api/invoices/?${params.toString()}`,
                {
                    method: "GET",
                    credentials: "same-origin",
                    headers: {
                        Accept: "application/json",
                    },
                }
            );


            const data = await response.json();


            if (!response.ok) {
                showError(
                    data?.detail ||
                    data?.message ||
                    "Unable to load invoices."
                );

                return;
            }


            const invoices = Array.isArray(data.results)
                ? data.results
                : [];


            if (!invoices.length) {
                emptyState.hidden = false;
                return;
            }


            renderInvoices(invoices);
            renderPagination(data);

        } catch (error) {
            showError(
                "Unable to connect to the server. Please try again."
            );

        } finally {
            loadingState.hidden = true;
        }
    };


    const reloadFromFirstPage = () => {
        currentPage = 1;
        loadInvoices();
    };


    let searchTimer;

    searchInput.addEventListener("input", () => {
        clearTimeout(searchTimer);

        searchTimer = setTimeout(
            reloadFromFirstPage,
            350
        );
    });


    statusInput.addEventListener(
        "change",
        reloadFromFirstPage
    );


    dateInput.addEventListener(
        "change",
        reloadFromFirstPage
    );


    clearButton.addEventListener("click", () => {
        searchInput.value = "";
        statusInput.value = "";
        dateInput.value = "";

        reloadFromFirstPage();
    });


    loadInvoices();
});

document.addEventListener("DOMContentLoaded", () => {
    const detailElement =
        document.getElementById("invoiceDetail");

    if (!detailElement) {
        return;
    }

    const invoiceId =
        window.location.pathname
            .split("/")
            .filter(Boolean)
            .pop();

    const loadingState =
        document.getElementById("invoiceDetailLoading");

    const errorState =
        document.getElementById("invoiceDetailError");

    const invoiceNumber =
        document.getElementById("invoiceDetailNumber");

    const invoiceDate =
        document.getElementById("invoiceDetailDate");

    const statusElement =
        document.getElementById("invoiceDetailStatus");

    const customerName =
        document.getElementById("invoiceCustomerName");

    const customerPhone =
        document.getElementById("invoiceCustomerPhone");

    const payeeName =
        document.getElementById("invoicePayeeName");

    const payeeAddress =
        document.getElementById("invoicePayeeAddress");

    const project =
        document.getElementById("invoiceProject");

    const plotArea =
        document.getElementById("invoicePlotArea");

    const plotRate =
        document.getElementById("invoicePlotRate");

    const plotCost =
        document.getElementById("invoicePlotCost");

    const amount =
        document.getElementById("invoiceAmount");

    const dueAmount =
        document.getElementById("invoiceDueAmount");

    const paymentType =
        document.getElementById("invoicePaymentType");

    const totalPaid =
        document.getElementById("invoiceTotalPaid");

    const paymentMode =
        document.getElementById("invoicePaymentMode");

    const transactionId =
        document.getElementById("invoiceTransactionId");

    const bankName =
        document.getElementById("invoiceBankName");

    const amountInWords =
        document.getElementById("invoiceAmountInWords");

    const pdfButton =
        document.getElementById("invoicePdfButton");


    const formatAmount = (value) => {
        if (value === null || value === undefined || value === "") {
            return "—";
        }

        const numericValue = Number(value);

        if (Number.isNaN(numericValue)) {
            return value;
        }

        return new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: "INR",
            minimumFractionDigits: 2,
        }).format(numericValue);
    };


    const formatDate = (value) => {
        if (!value) {
            return "—";
        }

        const date = new Date(`${value}T00:00:00`);

        if (Number.isNaN(date.getTime())) {
            return value;
        }

        return new Intl.DateTimeFormat("en-IN", {
            day: "2-digit",
            month: "long",
            year: "numeric",
        }).format(date);
    };


    const showError = (message) => {
        errorState.textContent = message;
        errorState.hidden = false;
    };


    const loadInvoice = async () => {
        try {
            const response = await fetch(
                `/api/invoices/${invoiceId}/`,
                {
                    method: "GET",
                    credentials: "same-origin",
                    headers: {
                        Accept: "application/json",
                    },
                }
            );


            const data = await response.json();


            if (!response.ok) {
                showError(
                    data?.detail ||
                    data?.message ||
                    "Unable to load invoice."
                );

                return;
            }


            invoiceNumber.textContent =
                data.invoice_number || "Invoice";


            invoiceDate.textContent =
                `Invoice date: ${formatDate(data.invoice_date)}`;


            statusElement.textContent =
                data.status || "";


            statusElement.className =
                `status-badge status-badge--${data.status || ""}`;


            customerName.textContent =
                data.customer_name || "Manual invoice";


            customerPhone.textContent =
                data.customer_phone || "—";


            payeeName.textContent =
                data.payee_name || "—";


            payeeAddress.textContent =
                data.payee_address || "—";


            project.textContent =
                data.project || "—";


            plotArea.textContent =
                data.plot_area || "—";


            plotRate.textContent =
                formatAmount(data.plot_rate);


            plotCost.textContent =
                formatAmount(data.plot_cost);


            amount.textContent =
                formatAmount(data.paid_amount);


            dueAmount.textContent =
                formatAmount(data.due_amount);


            paymentType.textContent =
                data.payment_type || "—";


            totalPaid.textContent =
                formatAmount(data.total_paid);


            paymentMode.textContent =
                data.payment_mode || "—";


            transactionId.textContent =
                data.transaction_id || "—";


            bankName.textContent =
                data.bank_name || "—";


            amountInWords.textContent =
                data.amount_in_words || "—";


            pdfButton.href =
                `/api/invoices/${invoiceId}/pdf/`;


            detailElement.hidden = false;

        } catch (error) {

            showError(
                "Unable to connect to the server. Please try again."
            );

        } finally {

            loadingState.hidden = true;
        }
    };


    loadInvoice();
});

document.addEventListener("DOMContentLoaded", () => {
    const form =
        document.getElementById("createInvoiceForm");

    if (!form) {
        return;
    }

    const customerSelect =
        document.getElementById("invoiceCustomer");

    const customerMode =
        document.getElementById("invoiceCustomerMode");

    const existingCustomerFields =
        document.getElementById("existingCustomerFields");

    const newCustomerFields =
        document.getElementById("newCustomerFields");

    const newCustomerName =
        document.getElementById("newCustomerName");

    const newCustomerPhone =
        document.getElementById("newCustomerPhone");

    const newCustomerAddress =
        document.getElementById("newCustomerAddress");

    const newCustomerProject =
        document.getElementById("newCustomerProject");

    const newCustomerPlotArea =
        document.getElementById("newCustomerPlotArea");

    const newCustomerPlotRate =
        document.getElementById("newCustomerPlotRate");

    const newCustomerPlotCost =
        document.getElementById("newCustomerPlotCost");

    const customerPreview =
        document.getElementById("customerPreview");

    const previewName =
        document.getElementById("previewCustomerName");

    const previewPhone =
        document.getElementById("previewCustomerPhone");

    const previewAddress =
        document.getElementById("previewCustomerAddress");

    const previewCustomerProject =
        document.getElementById("previewCustomerProject");

    const previewCustomerPlotArea =
        document.getElementById("previewCustomerPlotArea");

    const previewCustomerPlotRate =
        document.getElementById("previewCustomerPlotRate");

    const previewCustomerPlotCost =
        document.getElementById("previewCustomerPlotCost");

    const amountInput =
        document.getElementById("invoiceAmount");

    const dateInput =
        document.getElementById("invoiceDate");

    const statusInput =
        document.getElementById("invoiceStatus");

    // const projectInput =
    // document.getElementById("invoiceProject");

    // const plotAreaInput =
    //     document.getElementById("invoicePlotArea");

    // const plotRateInput =
    //     document.getElementById("invoicePlotRate");

    // const plotCostInput =
    //     document.getElementById("invoicePlotCost");

    // const paidAmountInput =
    //     document.getElementById("invoicePaidAmount");

    const dueAmountInput =
        document.getElementById("invoiceDueAmount");

    const paymentTypeInput =
        document.getElementById("invoicePaymentType");

    const totalPaidInput =
        document.getElementById("invoiceTotalPaid");

    const paymentModeInput =
        document.getElementById("invoicePaymentMode");

    const transactionIdInput =
        document.getElementById("invoiceTransactionId");

    const bankNameInput =
        document.getElementById("invoiceBankName");

    const submitButton =
        document.getElementById("createInvoiceSubmit");

    const errorBox =
        document.getElementById("createInvoiceError");

    let customers = [];


    const showError = (message) => {
        errorBox.textContent = message;
        errorBox.hidden = false;
    };


    const clearError = () => {
        errorBox.hidden = true;
        errorBox.textContent = "";
    };


    const showFieldErrors = (errors) => {
        Object.entries(errors || {}).forEach(
            ([field, messages]) => {

                const element =
                    form.querySelector(
                        `[data-error-for="${field}"]`
                    );

                if (!element) {
                    return;
                }


                element.textContent =
                    Array.isArray(messages)
                        ? messages.join(" ")
                        : String(messages);
            }
        );
    };


    const loadCustomers = async () => {
        try {
            const response = await fetch(
                "/api/customers/",
                {
                    credentials: "same-origin",
                    headers: {
                        Accept: "application/json",
                    },
                }
            );


            const data = await response.json();


            if (!response.ok) {
                showError(
                    data?.detail ||
                    data?.message ||
                    "Unable to load customers."
                );

                return;
            }


            customers = Array.isArray(data.results)
                ? data.results
                : Array.isArray(data)
                    ? data
                    : [];


            customers.forEach((customer) => {
                const option =
                    document.createElement("option");

                option.value = customer.id;

                option.textContent =
                    `${customer.name} — ${customer.phone}`;

                customerSelect.appendChild(option);
            });

        } catch (error) {
            showError(
                "Unable to load customers."
            );
        }
    };


    const updateCustomerPreview = () => {
        const customerId =
            Number(customerSelect.value);

        const customer =
            customers.find(
                (item) => item.id === customerId
            );


        if (!customer) {
            customerPreview.hidden = true;

            projectInput.value = "";
            plotAreaInput.value = "";
            plotRateInput.value = "";
            plotCostInput.value = "";

            return;
        }


        previewName.textContent =
            customer.name || "—";

        previewPhone.textContent =
            customer.phone || "—";

        previewAddress.textContent =
            customer.address || "—";

        previewCustomerProject.textContent =
            customer.project || "—";

        previewCustomerPlotArea.textContent =
            customer.plot_area || "—";

        previewCustomerPlotRate.textContent =
            customer.plot_rate || "—";

        previewCustomerPlotCost.textContent =
            customer.plot_cost || "—";

        // projectInput.value =
        //     customer.project || "";

        // plotAreaInput.value =
        //     customer.plot_area || "";

        // plotRateInput.value =
        //     customer.plot_rate || "";

        // plotCostInput.value =
        //     customer.plot_cost || "";

        customerPreview.hidden = false;
    };


    customerSelect.addEventListener(
        "change",
        updateCustomerPreview
    );

    const updateCustomerMode = () => {
        const isNewCustomer =
            customerMode.value === "new";

        existingCustomerFields.hidden = isNewCustomer;
        newCustomerFields.hidden = !isNewCustomer;

        if (isNewCustomer) {
            customerSelect.value = "";
            customerPreview.hidden = true;
        }
    };


    customerMode.addEventListener(
        "change",
        updateCustomerMode
    );


    form.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();

            clearError();

            const customerModeValue =
                customerMode.value;

            const customer =
                customerSelect.value;

            const amount =
                amountInput.value;

            const invoiceDate =
                dateInput.value;

            const status =
                statusInput.value;


            if (
                customerModeValue === "existing" &&
                !customer
            ) {
                showFieldErrors({
                    customer: [
                        "Please select a customer.",
                    ],
                });

                return;
            }


            if (customerModeValue === "new") {
                if (!newCustomerName.value.trim()) {
                    showError(
                        "Customer name is required."
                    );

                    newCustomerName.focus();

                    return;
                }

                if (!newCustomerPhone.value.trim()) {
                    showError(
                        "Customer phone is required."
                    );

                    newCustomerPhone.focus();

                    return;
                }

                if (!newCustomerAddress.value.trim()) {
                    showError(
                        "Customer address is required."
                    );

                    newCustomerAddress.focus();

                    return;
                }
            }

            if (!amount) {
                showFieldErrors({
                    amount: [
                        "Amount is required.",
                    ],
                });

                return;
            }


            if (!invoiceDate) {
                showFieldErrors({
                    invoice_date: [
                        "Invoice date is required.",
                    ],
                });

                return;
            }


            submitButton.disabled = true;
            submitButton.textContent =
                "Creating...";


            try {

                const csrfToken =
                    form.querySelector(
                        'input[name="csrfmiddlewaretoken"]'
                    ).value;


                const response = await fetch(
                    "/api/invoices/",
                    {
                        method: "POST",

                        credentials: "same-origin",

                        headers: {
                            "Content-Type":
                                "application/json",

                            "X-CSRFToken":
                                csrfToken,

                            Accept:
                                "application/json",
                        },

                        body: JSON.stringify(
                            {
                                ...(customerModeValue === "existing"
                                    ? {
                                        customer: Number(customer),
                                    }
                                    : {
                                        new_customer: {
                                            name:
                                                newCustomerName.value.trim(),

                                            phone:
                                                newCustomerPhone.value.trim(),

                                            address:
                                                newCustomerAddress.value.trim(),

                                            project:
                                                newCustomerProject.value.trim(),

                                            plot_area:
                                                newCustomerPlotArea.value.trim(),

                                            plot_rate:
                                                newCustomerPlotRate.value || null,

                                            plot_cost:
                                                newCustomerPlotCost.value || null,
                                        },
                                    }),

                                paid_amount: amount,
                            paid_amount: amount,
                            invoice_date: invoiceDate,
                            status: status,

                            // paid_amount: paidAmountInput.value || null,
                            due_amount: dueAmountInput.value || null,
                            payment_type: paymentTypeInput.value.trim(),
                            total_paid: totalPaidInput.value || null,
                            payment_mode: paymentModeInput.value.trim(),
                            transaction_id: transactionIdInput.value.trim(),
                            bank_name: bankNameInput.value.trim(),
                        }),
                    }
                );


                const data =
                    await response.json();


                if (!response.ok) {

                    if (data?.errors) {
                        showFieldErrors(
                            data.errors
                        );
                    }

                    showError(
                        data?.message ||
                        data?.detail ||
                        "Unable to create invoice."
                    );

                    return;
                }


                window.location.href =
                    `/admin-invoices/${data.id}/`;


            } catch (error) {
                console.error("Invoice creation error:", error);
                showError(error.message || "Unable to connect to server.");

            } finally {

                submitButton.disabled = false;
                submitButton.textContent =
                    "Create Invoice";
            }
        }
    );


    loadCustomers();
});

// ----------------------------------------------------ASSOCIATE LOGIN
document.addEventListener("DOMContentLoaded", () => {
    const form =
        document.getElementById("associateLoginForm");

    if (!form) {
        return;
    }

    const associateIdInput =
        document.getElementById("associateId");

    const passwordInput =
        document.getElementById("associatePassword");

    const submitButton =
        document.getElementById("associateLoginSubmit");

    const errorBox =
        document.getElementById("associateLoginError");


    const getCsrfToken = () => {
        const tokenInput = form.querySelector(
            'input[name="csrfmiddlewaretoken"]'
        );

        return tokenInput
            ? tokenInput.value
            : "";
    };


    const clearErrors = () => {
        errorBox.hidden = true;
        errorBox.textContent = "";

        form.querySelectorAll(
            ".form-field__error"
        ).forEach((element) => {
            element.textContent = "";
        });
    };


    const showError = (message) => {
        errorBox.textContent = message;
        errorBox.hidden = false;
    };


    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        clearErrors();

        const associateId =
            associateIdInput.value.trim();

        const password =
            passwordInput.value;


        if (!associateId) {
            showError("Associate ID is required.");
            associateIdInput.focus();
            return;
        }


        if (!password) {
            showError("Password is required.");
            passwordInput.focus();
            return;
        }


        submitButton.disabled = true;
        submitButton.textContent = "Signing in...";


        try {
            const response = await fetch(
                "/api/accounts/login/associate/",
                {
                    method: "POST",

                    credentials: "same-origin",

                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(),
                    },

                    body: JSON.stringify({
                        associate_id: associateId,
                        password,
                    }),
                }
            );


            const data = await response.json();


            if (!response.ok) {
                showError(
                    data?.detail ||
                    data?.message ||
                    (
                        Array.isArray(data)
                            ? data.join(" ")
                            : "Unable to sign in."
                    )
                );

                return;
            }


            /*
             * Associate portal destination is not being invented here.
             * The current product scope defines associate authentication,
             * profile editing and password change, but no confirmed
             * frontend portal route exists yet.
             */
            window.location.href =
                "/associate/profile/";

        } catch (error) {

            showError(
                "Unable to connect to the server. Please try again."
            );

        } finally {

            submitButton.disabled = false;
            submitButton.textContent = "Sign In";
        }
    });
});