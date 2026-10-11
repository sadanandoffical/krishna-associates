# Krishna Associates — Project Progress Ledger

> Canonical implementation progress/context file.
>
> This file is maintained alongside the Coding-Agent Master Product Specification.
> A coding agent must read this file before starting implementation work.
>
> Last updated: 2026-09-13
> Last verified milestone: Step 5.6 — Sites API final hardening

---

# 1. Project Identity

**Product:** Krishna Associates Webapp

**Business:** Real-estate / plot sales

**Primary public market:** Lucknow, Uttar Pradesh, India

**Commercial scope:**
- Property/site discovery
- Plot/property sales
- Visitor enquiries/contact
- WhatsApp contact
- Associate login/profile
- Admin operations
- Customer management
- Invoice/payment acknowledgement
- Invoice PDF/export

**Explicit non-goal:**
- Rentals are NOT part of the product.

---

# 2. Canonical Specifications

The following documents are authoritative:

1. `Krishna_Associates_Coding_Agent_Master_Spec.docx`
2. `KRISHNA_ASSOCIATES_FRONTEND_DESIGN_SPEC.md`

The frontend design specification controls the visual/UX direction.

The Coding-Agent Master Product Specification controls product scope,
architecture principles, backend expectations, lifecycle, and unresolved decisions.

If a newer explicit product decision conflicts with an older assumption,
the newer explicit decision wins.

---

# 3. Development Rules

Every meaningful feature must follow:

1. Read context
2. Inspect existing implementation
3. Reconcile requested work with existing code
4. Plan the smallest coherent slice
5. Implement
6. Run targeted verification
7. Integrate with existing architecture
8. Update this progress ledger
9. Perform loose-end review

Do not:
- rebuild working functionality without reason
- silently invent unspecified business rules
- add rental functionality
- create unnecessary third-party dependencies
- rely only on frontend permissions
- leave untested critical paths
- leave undocumented assumptions
- mark a feature complete merely because an API/screen exists

---

# 4. Current Overall Status

## Phase

**Module implementation — backend foundation/domain APIs**

## Current completed modules

| Area | Status |
|---|---|
| Django bootstrap | COMPLETE |
| Core database architecture | COMPLETE |
| Authentication & authorization | COMPLETE |
| API foundation | COMPLETE |
| Cities API | COMPLETE |
| Sites API | COMPLETE |
| Site dynamic features | COMPLETE |
| Site gallery/media | COMPLETE |
| Site map image | COMPLETE |
| Site API hardening | COMPLETE |
| Associates API | Foundation COMPLETE |
| Customers | NOT STARTED |
| Invoices | NOT STARTED |
| PDF/export | NOT STARTED |
| Enquiry/contact | NOT STARTED |
| Public frontend | NOT STARTED |
| Admin frontend | NOT STARTED |
| Associate frontend | NOT STARTED |
| QA/release | NOT STARTED |

---

# 5. Completed Development Steps

## STEP 1 — Bootstrap

**Status: COMPLETE**

Implemented:

- New Django project created from scratch
- Django apps established:
  - `accounts`
  - `cities`
  - `sites`
  - `customers`
  - `invoices`
  - `enquiries`
- PostgreSQL configuration
- Environment variable configuration
- DRF foundation
- Django filter integration
- Media/static configuration
- Templates/static directories
- `.env`
- `.env.example`
- `.gitignore`
- `PROJECT_PROGRESS.md`

Installed core dependencies:

- Django
- djangorestframework
- django-filter
- psycopg[binary]
- Pillow
- python-dotenv

PDF dependency intentionally deferred until invoice/PDF implementation.

---

# 6. STEP 2 — Core Database Architecture

**Status: COMPLETE**

## Accounts

Implemented custom user model:

```text
accounts.User