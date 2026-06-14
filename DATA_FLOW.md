# Jovira Backend — Complete Data Flow & Relationship Reference

> **Purpose:** This document describes every entity, relationship, and API flow in the Jovira backend so that an AI (or developer) can fully understand the system and suggest code modifications.

---

## Table of Contents

1. [Tech Stack & Architecture](#1-tech-stack--architecture)
2. [URL Structure](#2-url-structure)
3. [Authentication Flow](#3-authentication-flow)
4. [Accounts — Users](#4-accounts--users)
5. [Agencies — Agency Registration & Approval](#5-agencies--agency-registration--approval)
6. [Finance — Currencies, Exchange Rates, Invoices](#6-finance--currencies-exchange-rates-invoices)
7. [Inventory — Hotels, Flights, Transfers, Excursions, Tour Packages](#7-inventory)
   - [7.1 Hotels](#71-hotels)
   - [7.2 Flights](#72-flights)
   - [7.3 Transfers](#73-transfers)
   - [7.4 Excursions](#74-excursions)
   - [7.5 Tour Packages](#75-tour-packages)
8. [Reservations — Core Booking System](#8-reservations--core-booking-system)
   - [8.1 Reservation](#81-reservation)
   - [8.2 Tourist](#82-tourist)
   - [8.3 Hotel Booking](#83-hotel-booking)
   - [8.4 Flight Ticket](#84-flight-ticket)
   - [8.5 Excursion Booking](#85-excursion-booking)
   - [8.6 Transfer Service](#86-transfer-service)
   - [8.7 Excursion Service (Standalone)](#87-excursion-service-standalone)
9. [End-to-End Flows](#9-end-to-end-flows)
   - [9.1 Register a Normal User](#91-register-a-normal-user)
   - [9.2 Register an Agency](#92-register-an-agency)
   - [9.3 Approve an Agency](#93-approve-an-agency)
   - [9.4 Create a Reservation with Tourists](#94-create-a-reservation-with-tourists)
   - [9.5 Add a Hotel Booking to a Reservation](#95-add-a-hotel-booking-to-a-reservation)
   - [9.6 Add a Flight Ticket to a Reservation](#96-add-a-flight-ticket-to-a-reservation)
   - [9.7 Add an Excursion Booking to a Reservation](#97-add-an-excursion-booking-to-a-reservation)
   - [9.8 Add a Transfer Service to a Reservation](#98-add-a-transfer-service-to-a-reservation)
   - [9.9 Cancel a Hotel Booking](#99-cancel-a-hotel-booking)
   - [9.10 Cancel an Entire Reservation](#910-cancel-an-entire-reservation)
   - [9.11 Book a Standalone Excursion Service](#911-book-a-standalone-excursion-service)
10. [Price Visibility Rules](#10-price-visibility-rules)
11. [Hotel Room Availability Logic](#11-hotel-room-availability-logic)
12. [Complete Entity-Relationship Summary](#12-complete-entity-relationship-summary)
13. [All API Endpoints Reference](#13-all-api-endpoints-reference)

---

## 1. Tech Stack & Architecture

| Layer | Technology |
|-------|------------|
| Framework | Django + Django REST Framework |
| Auth | JWT via `rest_framework_simplejwt` |
| API Docs | `drf_spectacular` (Swagger UI at `/api/schema/swagger-ui/`) |
| Translations | `modeltranslation` (supports `_en`, `_tr`, `_ru` field variants) |
| Database | SQLite (development) |
| Media | Django media serving (`/media/`) |

**Apps:**
- `accounts` — Custom user model & auth
- `agencies` — Agency management
- `inventory` — Hotels, Flights, Transfers, Excursions, Tour Packages
- `reservations` — All booking logic
- `finance` — Currencies, Exchange Rates, Invoices
- `publicsite` — Public-facing homepage content (HeroSection)

---

## 2. URL Structure

All API routes are prefixed with `/api/v1/`.

```
/api/v1/auth/login/              POST  — Obtain JWT token pair
/api/v1/auth/refresh/            POST  — Refresh access token
/api/v1/auth/register/           POST  — Register a normal user

/api/v1/accounts/admin/...       Admin user management
/api/v1/accounts/client/...      Authenticated user self-management

/api/v1/agencies/admin/...       Admin agency management
/api/v1/agencies/client/...      Public agency browsing
/api/v1/agencies/client/register/  POST — Register a new agency

/api/v1/inventory/admin/...      Admin inventory management
/api/v1/inventory/client/...     Public/authenticated inventory browsing

/api/v1/reservations/admin/...   Admin reservation management
/api/v1/reservations/client/...  Authenticated reservation management

/api/v1/finance/admin/...        Admin finance management
/api/v1/finance/client/...       Public/authenticated finance info

/api/v1/public-site/...          Public homepage content
/admin/                          Django admin panel
```

---

## 3. Authentication Flow

Authentication uses **JWT (JSON Web Tokens)**. There is no username — login is done with **email + password**.

### Login
```
POST /api/v1/auth/login/
Body: { "email": "user@example.com", "password": "yourpassword" }
Response: { "access": "<jwt_token>", "refresh": "<refresh_token>" }
```

### Use Token
Send the access token in every protected request:
```
Authorization: Bearer <access_token>
```

### Refresh Token
```
POST /api/v1/auth/refresh/
Body: { "refresh": "<refresh_token>" }
Response: { "access": "<new_access_token>" }
```

### Permission Levels
| Level | Description | How Detected |
|-------|-------------|--------------|
| Public / Anonymous | No token needed | `AllowAny` |
| Authenticated | Any valid user | `IsAuthenticated` |
| Admin/Staff | Django staff/superuser | `IsAdminUser` |
| Agency | `role == AGENCY` AND assigned to an agency | `can_access_agency_prices` property |

---

## 4. Accounts — Users

### Model: `CustomUser`

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `email` | EmailField (unique) | Used as USERNAME_FIELD (no username) |
| `first_name` | CharField | |
| `last_name` | CharField | |
| `phone_number` | CharField (nullable) | |
| `role` | CharField choices | `NORMAL`, `AGENCY`, `STAFF` |
| `agency` | FK → Agency (nullable) | Assigned when role is AGENCY |
| `is_active` | BooleanField | Set to False until agency is approved |
| `is_staff` | BooleanField | Django staff flag |
| `is_superuser` | BooleanField | Full permissions |

### Roles Explained
- **NORMAL** — Regular end-user, sees public prices only, creates reservations without agency
- **AGENCY** — Linked to an Agency record, sees agency prices, reservations auto-tagged with their agency
- **STAFF** — Internal staff, sees agency prices (same as AGENCY access level)

### `can_access_agency_prices` Property
Returns `True` if the user is `is_superuser`, `is_staff`, or has role `AGENCY` or `STAFF`.

### Register a Normal User
```
POST /api/v1/auth/register/
Body:
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "password": "securepassword",
  "password2": "securepassword"
}
```
- Role is automatically set to `NORMAL`
- `agency` is automatically set to `null`
- Password must be at least 8 characters and must match `password2`

### Admin User Management
```
GET    /api/v1/accounts/admin/users/          — List all users
POST   /api/v1/accounts/admin/users/          — Create user
GET    /api/v1/accounts/admin/users/{id}/     — Get user
PUT    /api/v1/accounts/admin/users/{id}/     — Full update (including role, agency, is_staff)
PATCH  /api/v1/accounts/admin/users/{id}/     — Partial update
DELETE /api/v1/accounts/admin/users/{id}/     — Delete user
```

### Client (Self) User Management
```
GET   /api/v1/accounts/client/users/{id}/    — View own profile
PUT   /api/v1/accounts/client/users/{id}/    — Update own profile (name, phone only)
PATCH /api/v1/accounts/client/users/{id}/    — Partial update own profile
```
- `role`, `agency`, `is_active` are **read-only** for client

---

## 5. Agencies — Agency Registration & Approval

### Model: `Agency`

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `name` | CharField | Agency name |
| `agency_type` | CharField | Type label (e.g., "Tour Operator") |
| `contact_person` | CharField | Primary contact name |
| `email` | EmailField (nullable) | Agency contact email |
| `phone` | CharField (nullable) | |
| `mobile_phone` | CharField (nullable) | |
| `skype_id` | CharField (nullable) | |
| `icq` | CharField (nullable) | |
| `is_approved` | BooleanField | Default: `False`. Must be approved by admin |
| `approved_at` | DateTimeField (nullable) | Set on first approval |

### Agency Registration Flow
```
POST /api/v1/agencies/client/register/
Body:
{
  "name": "Sunshine Tours",
  "agency_type": "Tour Operator",
  "contact_person": "Jane Smith",
  "email": "info@sunshinetours.com",
  "phone": "+90123456789",
  "mobile_phone": "+90987654321",
  "skype_id": "sunshine.tours",
  "icq": "",
  "account_email": "jane@sunshinetours.com",
  "account_first_name": "Jane",
  "account_last_name": "Smith",
  "account_phone_number": "+90987654321",
  "password": "securepassword",
  "password2": "securepassword"
}
```
**What happens:**
1. Agency record is created with `is_approved = False`
2. A `CustomUser` is created with `role = AGENCY`, linked to the new agency, `is_active = False`
3. The agency account **cannot log in** until approved by admin

### Agency Approval Flow (Admin only)
```
POST /api/v1/agencies/admin/agencies/{id}/approve/
```
**What happens:**
1. `agency.is_approved = True`, `agency.approved_at` = now
2. All users linked to this agency with `role = AGENCY` have `is_active = True` (can now log in)

### Admin Agency Management
```
GET    /api/v1/agencies/admin/agencies/          — List all agencies
POST   /api/v1/agencies/admin/agencies/          — Create agency manually
GET    /api/v1/agencies/admin/agencies/{id}/     — Get agency details
PUT    /api/v1/agencies/admin/agencies/{id}/     — Full update
PATCH  /api/v1/agencies/admin/agencies/{id}/     — Partial update
DELETE /api/v1/agencies/admin/agencies/{id}/     — Delete agency
POST   /api/v1/agencies/admin/agencies/{id}/approve/ — Approve agency
```

### Client Agency Browsing (Public, no auth)
```
GET /api/v1/agencies/client/agencies/        — List all approved agencies
GET /api/v1/agencies/client/agencies/{id}/   — Get approved agency details
```
Only `is_approved = True` agencies are visible. `is_approved` and `approved_at` fields are hidden from clients.

---

## 6. Finance — Currencies, Exchange Rates, Invoices

### Model: `Currency`

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `code` | CharField (3 chars, unique) | e.g., `USD`, `TRY`, `EUR` |
| `name` | CharField | e.g., `US Dollar` |
| `symbol` | CharField (5 chars) | e.g., `$` |
| `is_active` | BooleanField | Only active currencies shown to clients |

### Model: `ExchangeRate`

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `base_currency` | FK → Currency | |
| `target_currency` | FK → Currency | |
| `rate` | DecimalField | How many target = 1 base |
| `last_updated` | DateTimeField (auto) | |

Unique constraint: `(base_currency, target_currency)` pair.

### Currency Conversion Utility
Used internally across the system (e.g., TourPackage cost floor calculation):
```
GET /api/v1/finance/client/convert/?from=USD&to=TRY&amount=100
Response: { "from": "USD", "to": "TRY", "amount": "100", "converted_amount": "3250.00", "effective_rate": "32.5" }
```

### Model: `Invoice`

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `reservation` | OneToOne FK → Reservation | One invoice per reservation |
| `net_amount` | DecimalField | Total cost/net |
| `sale_amount` | DecimalField | Total selling price |
| `profit` | DecimalField | sale - net |
| `agency_commission` | DecimalField | Commission to agency |
| `is_paid` | BooleanField | Payment tracking |

### Finance Endpoints
```
# Admin
GET/POST/PUT/PATCH/DELETE /api/v1/finance/admin/currencies/
GET/POST/PUT/PATCH/DELETE /api/v1/finance/admin/exchange-rates/
GET/POST/PUT/PATCH/DELETE /api/v1/finance/admin/invoices/

# Client (read-only)
GET /api/v1/finance/client/currencies/
GET /api/v1/finance/client/exchange-rates/
GET /api/v1/finance/client/invoices/
GET /api/v1/finance/client/convert/?from=USD&to=TRY&amount=100
```

---

## 7. Inventory

### 7.1 Hotels

#### Models involved: `Hotel`, `HotelFeature`, `HotelImage`, `HotelRoom`

**`HotelFeature`** — Tags like "Pool", "Spa", "WiFi"

| Field | Type |
|-------|------|
| `id` | Auto PK |
| `name` | CharField (+ `name_en`, `name_tr`, `name_ru` via modeltranslation) |

---

**`Hotel`**

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `name` | CharField (+ translations) | |
| `city` | CharField (+ translations) | |
| `stars` | IntegerField | 1–5 |
| `description` | TextField (+ translations, nullable) | |
| `main_image` | ImageField | Upload to `hotels/main/` |
| `features` | M2M → HotelFeature | Amenities/tags |

Related: `gallery_images` (reverse of HotelImage), `rooms` (reverse of HotelRoom)

---

**`HotelImage`** — Gallery images for a hotel

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `hotel` | FK → Hotel | |
| `image` | ImageField | Upload to `hotels/gallery/` |
| `alt_text` | CharField | |
| `order` | PositiveIntegerField | Display order |

---

**`HotelRoom`** — A specific room type with pricing for a date window

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `hotel` | FK → Hotel | |
| `room_type` | CharField | `SINGLE`, `DOUBLE`, `TRIPLE`, `FAMILY`, `SUITE` |
| `board_type` | CharField | `RO`, `BB`, `HB`, `FB`, `ALL`, `UALL` |
| `date_from` | DateField | Start of availability window |
| `date_to` | DateField | End of availability window |
| `availability_count` | PositiveIntegerField | Total rooms in stock |
| `currency` | FK → Currency | |
| `public_price` | DecimalField | Price for normal users |
| `agency_price` | DecimalField (nullable) | Price for agency users |
| `cost_price` | DecimalField (nullable) | Internal cost (hidden from client) |
| `note` | TextField | |

**Room Capacity Map (used in booking validation):**
- SINGLE → 1 person
- DOUBLE → 2 persons
- TRIPLE → 3 persons
- FAMILY → 4 persons
- SUITE → 4 persons

### Hotel Endpoints

```
# Admin (full CRUD)
GET/POST/PUT/PATCH/DELETE /api/v1/inventory/admin/hotels/
GET/POST/PUT/PATCH/DELETE /api/v1/inventory/admin/hotel-rooms/
GET/POST/PUT/PATCH/DELETE /api/v1/inventory/admin/hotel-images/

# Filter hotel rooms by hotel:
GET /api/v1/inventory/admin/hotel-rooms/?hotel={hotel_id}

# Check room availability:
GET /api/v1/inventory/admin/hotel-rooms/{id}/availability/?check_in=2025-06-01&check_out=2025-06-07
# Response: { hotel_room, check_in, check_out, total_count, confirmed_count, pending_count, booked_count, available_count }

# Client (read-only)
GET /api/v1/inventory/client/hotels/
GET /api/v1/inventory/client/hotels/{id}/
GET /api/v1/inventory/client/hotel-rooms/
GET /api/v1/inventory/client/hotel-rooms/{id}/
GET /api/v1/inventory/client/hotel-rooms/{id}/availability/?check_in=...&check_out=...
```

---

### 7.2 Flights

#### Model: `Flight`

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `flight_number` | CharField | e.g., `TK101` |
| `airline` | CharField (+ translations) | |
| `origin` | CharField (+ translations) | |
| `destination` | CharField (+ translations) | |
| `departure_time` | DateTimeField | |
| `arrival_time` | DateTimeField | |
| `currency` | FK → Currency (nullable) | |
| `price` | DecimalField (nullable) | Public price |
| `agency_price` | DecimalField (nullable) | Agency price |
| `cost_price` | DecimalField (nullable) | Internal cost |

### Flight Endpoints
```
# Admin (full CRUD)
GET/POST/PUT/PATCH/DELETE /api/v1/inventory/admin/flights/

# Client (read-only, price depends on user role)
GET /api/v1/inventory/client/flights/
GET /api/v1/inventory/client/flights/{id}/
```

---

### 7.3 Transfers

#### Models: `TransferProvider`, `Transfer`

**`TransferProvider`** — The company or individual providing transfer services

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `name` | CharField | |
| `provider_type` | CharField | `COMPANY` or `INDIVIDUAL` |
| `contact_person` | CharField | |
| `phone` | CharField | |
| `email` | EmailField | |
| `notes` | TextField | |

---

**`Transfer`** — A specific transfer route from provider catalog

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `provider` | FK → TransferProvider | |
| `name` | CharField | Transfer name/label |
| `from_location` | CharField | Origin point |
| `to_location` | CharField | Destination point |
| `vehicle_type` | CharField | e.g., "Van", "Minibus" |
| `capacity` | PositiveIntegerField (nullable) | Max passengers |
| `currency` | FK → Currency (nullable) | |
| `public_price` | DecimalField (nullable) | |
| `agency_price` | DecimalField (nullable) | |
| `cost_price` | DecimalField (nullable) | Internal cost |

### Transfer Endpoints
```
# Admin (full CRUD)
GET/POST/PUT/PATCH/DELETE /api/v1/inventory/admin/transfer-providers/
GET/POST/PUT/PATCH/DELETE /api/v1/inventory/admin/transfers/

# Client (read-only)
GET /api/v1/inventory/client/transfers/
GET /api/v1/inventory/client/transfers/{id}/
```

---

### 7.4 Excursions

#### Model: `Excursion`

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `name` | CharField (+ translations) | |
| `city` | CharField (+ translations) | |
| `duration_hours` | DecimalField | e.g., `3.50` for 3.5 hours |
| `currency` | FK → Currency (nullable) | |
| `public_price` | DecimalField (nullable) | |
| `agency_price` | DecimalField (nullable) | |
| `cost_price` | DecimalField (nullable) | Internal cost |

### Excursion Endpoints
```
# Admin (full CRUD)
GET/POST/PUT/PATCH/DELETE /api/v1/inventory/admin/excursions/

# Client (read-only)
GET /api/v1/inventory/client/excursions/
GET /api/v1/inventory/client/excursions/{id}/
```

---

### 7.5 Tour Packages

#### Model: `TourPackage`

A pre-built bundle linking flights, hotels, transfers, and excursions.

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `name` | CharField (+ translations) | |
| `destination` | CharField (+ translations) | |
| `days` | IntegerField | |
| `nights` | IntegerField | |
| `currency` | FK → Currency (nullable) | Package base currency |
| `public_price` | DecimalField (nullable) | |
| `agency_price` | DecimalField (nullable) | |
| `cost_price` | DecimalField (nullable) | Must be >= sum of component costs |
| `flights` | M2M → Flight | |
| `hotels` | M2M → Hotel | |
| `transfers` | M2M → Transfer | |
| `excursions` | M2M → Excursion | |

**Cost Floor Validation (`clean()`):**
- `cost_price` cannot be lower than the sum of all component `cost_price` values (flights + transfers + excursions), converted to package currency
- `agency_price` and `public_price` also cannot be lower than this floor
- `public_price` cannot be lower than `agency_price`

### Tour Package Endpoints
```
# Admin (full CRUD)
GET/POST/PUT/PATCH/DELETE /api/v1/inventory/admin/tour-packages/

# Client (read-only)
GET /api/v1/inventory/client/tour-packages/
GET /api/v1/inventory/client/tour-packages/{id}/
```
Response includes `minimum_cost_floor` (read-only, calculated).

---

## 8. Reservations — Core Booking System

### Relationships Overview

```
Reservation
  ├── Agency (optional FK)
  ├── TourPackage (optional FK)
  ├── Currency (FK)
  ├── tourists[]  ← Tourist (FK → Reservation)
  ├── hotel_bookings[]  ← HotelBooking (FK → Reservation)
  │     └── hotel_room (FK → HotelRoom)
  │     └── tourists[] (M2M → Tourist)
  ├── flight_tickets[]  ← FlightTicket (FK → Reservation)
  │     └── flight (FK → Flight)
  │     └── tourist (FK → Tourist)
  ├── excursion_bookings[]  ← ExcursionBooking (FK → Reservation)
  │     └── excursion (FK → Excursion)
  │     └── tourists[] (M2M → Tourist)
  └── transfer_services[]  ← TransferService (FK → Reservation)
        └── transfer (optional FK → Transfer catalog)
        └── passengers[] (M2M → Tourist)

ExcursionService  ← Standalone, not linked to any Reservation
  └── excursion (FK → Excursion)
```

---

### 8.1 Reservation

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `reservation_number` | CharField (unique) | Must be provided on creation |
| `created_at` | DateTimeField (auto) | Read-only |
| `currency` | FK → Currency | The billing currency of this reservation |
| `status` | CharField | `DRAFT`, `ON_PROCESS`, `CONFIRMED`, `CANCELED` |
| `agency` | FK → Agency (nullable) | Set automatically for AGENCY users |
| `tour_package` | FK → TourPackage (nullable) | Optional link to a package |

**Status flow:**
```
DRAFT → ON_PROCESS → CONFIRMED
          ↓              ↓
        CANCELED      CANCELED
```

**Agency auto-assignment rules:**
- If the request user has `role = AGENCY`: `agency` is automatically set to their own agency (cannot be overridden)
- If the request user has `role = NORMAL`: `agency` is set to `null`
- Admin users can set any agency value freely

**The `tourists[]` array in Reservation** allows creating/updating tourists inline when creating/updating the reservation.

---

### 8.2 Tourist

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `reservation` | FK → Reservation | |
| `first_name` | CharField | |
| `last_name` | CharField | |
| `sex` | CharField | `MALE`, `FEMALE` |
| `age_type` | CharField | `ADULT`, `CHILD`, `INFANT` |
| `passport_number` | CharField (optional) | |
| `nationality` | CharField (optional) | |
| `birth_date` | DateField (nullable) | |
| `passport_expiry_date` | DateField (nullable) | |

**Important:** A Tourist always belongs to exactly one Reservation. When assigning tourists to HotelBooking, ExcursionBooking, or TransferService, all assigned tourists must belong to the **same** reservation.

---

### 8.3 Hotel Booking

Links a Reservation to a specific HotelRoom for specific dates.

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `reservation` | FK → Reservation | |
| `hotel_room` | FK → HotelRoom | The specific room type booked |
| `check_in_date` | DateField | |
| `check_out_date` | DateField | Must be after check_in_date |
| `quantity` | PositiveIntegerField | Number of rooms |
| `status` | CharField | `PENDING`, `CONFIRMED`, `CANCELLED` |
| `tourists` | M2M → Tourist | Guests in these rooms |
| `selling_currency` | FK → Currency (nullable) | Currency used for billing |
| `price` | DecimalField (nullable) | Public price |
| `agency_price` | DecimalField (nullable) | Agency price |
| `cost_currency` | FK → Currency (nullable) | |
| `cost` | DecimalField (nullable) | Internal cost |
| `cross_currency_rate` | DecimalField | Default 1.0 |
| `confirm_booking_number` | CharField | Supplier confirmation number |
| `agent_confirmation_number` | CharField | Agent's own reference |
| `hotel_cancellation_number` | CharField | Used when cancelling |
| `internal_note` | TextField | Private notes |
| `remarks_for_hotel` | TextField | Notes sent to hotel |
| `is_paid` | BooleanField | Payment status |

**Availability side effects:**
- **Create** with non-CANCELLED status → `hotel_room.availability_count -= quantity`
- **Delete** (non-CANCELLED booking) → `hotel_room.availability_count += quantity`
- **Update status to CANCELLED** → restores availability
- **Update status from CANCELLED to active** → deducts availability again
- **Change quantity** → adjusts the difference atomically
- **Change room** → restores old room, deducts new room

**Validation rules:**
- `check_out_date` must be after `check_in_date`
- Both dates must fall within the room's `date_from`–`date_to` window
- `quantity` must not exceed available rooms (excluding own booking when updating)
- All assigned tourists must belong to the same reservation
- Number of tourists cannot exceed `capacity_per_room × quantity`

---

### 8.4 Flight Ticket

Links one Tourist to one Flight within a Reservation. One record = one ticket for one person.

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `reservation` | FK → Reservation | |
| `flight` | FK → Flight | |
| `tourist` | FK → Tourist | One ticket per tourist |
| `ticket_number` | CharField | Airline ticket number |
| `pnr_code` | CharField | Booking reference code |

**Note:** To book multiple tourists on the same flight, create multiple `FlightTicket` records (one per tourist).

---

### 8.5 Excursion Booking

Links one or more tourists to an Excursion within a Reservation.

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `reservation` | FK → Reservation | |
| `excursion` | FK → Excursion | |
| `tourists` | M2M → Tourist | All tourists going on this excursion |
| `tour_date` | DateField | Date of the excursion |
| `pickup_time` | TimeField (nullable) | Pickup time |

---

### 8.6 Transfer Service

A transfer leg within a Reservation. Can optionally link to a catalog Transfer or be fully manual.

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `reservation` | FK → Reservation | |
| `transfer` | FK → Transfer (nullable) | Optional catalog link (auto-fills prices) |
| `tour_package` | FK → TourPackage (nullable) | If part of a package |
| `service_name` | CharField | Displayed name of service |
| `service_date` | DateField | |
| `on_arrival` | BooleanField | Arrival direction |
| `on_departure` | BooleanField | Departure direction |
| `from_location_type` | CharField | `AIRPORT`, `TERMINAL`, `HOTEL` |
| `from_location_name` | CharField | Name of origin location |
| `to_location_type` | CharField | `AIRPORT`, `TERMINAL`, `HOTEL` |
| `to_location_name` | CharField | Name of destination location |
| `price` | DecimalField | Public price |
| `agency_price` | DecimalField (nullable) | Agency price |
| `currency` | FK → Currency | |
| `passengers` | M2M → Tourist | Who is in this transfer |
| `external_note` | TextField | Notes visible externally |
| `driver_note` | TextField | Notes for the driver |

**Constraint:** At least one of `on_arrival` or `on_departure` must be `True` (enforced at DB level too).

**Validation rules:**
- At least one of `on_arrival` / `on_departure` must be true
- If the reservation has a `tour_package` and a `tour_package` is set here, they must match
- All passengers must belong to the same reservation

---

### 8.7 Excursion Service (Standalone)

A standalone excursion booking **not linked to any Reservation**. Used for walk-in or ad-hoc excursion sales.

| Field | Type | Notes |
|-------|------|-------|
| `id` | Auto PK | |
| `system_date` | DateTimeField (auto) | Read-only, auto set on create |
| `excursion_date` | DateField | |
| `excursion` | FK → Excursion | |
| `is_combo` | BooleanField | Whether this is a combo excursion |
| `pickup_point` | CharField (nullable) | |
| `price` | DecimalField | Default 0 |
| `selling_currency` | FK → Currency | |
| `cost` | DecimalField | Default 0 |
| `cost_currency` | FK → Currency | |
| `cross_currency_rate` | DecimalField | Default 1.0 |
| `is_paid` | BooleanField | |
| `confirm_booking_number` | CharField (nullable) | |
| `agent_confirmation_number` | CharField (nullable) | |
| `note` | TextField (nullable) | |

---

## 9. End-to-End Flows

### 9.1 Register a Normal User

```
POST /api/v1/auth/register/
{
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+905551234567",
  "password": "mypassword123",
  "password2": "mypassword123"
}
```
→ User created with `role=NORMAL`, `agency=null`, `is_active=True`

```
POST /api/v1/auth/login/
{ "email": "john@example.com", "password": "mypassword123" }
→ { "access": "...", "refresh": "..." }
```

---

### 9.2 Register an Agency

```
POST /api/v1/agencies/client/register/
{
  "name": "Sunshine Tours",
  "agency_type": "Tour Operator",
  "contact_person": "Jane Smith",
  "email": "info@sunshine.com",
  "phone": "+905551234567",
  "account_email": "jane@sunshine.com",
  "account_first_name": "Jane",
  "account_last_name": "Smith",
  "password": "securepass123",
  "password2": "securepass123"
}
```
→ Agency created with `is_approved=False`
→ User created with `role=AGENCY`, `is_active=False`
→ **Cannot log in until admin approves**

---

### 9.3 Approve an Agency

```
# Admin must be logged in
POST /api/v1/agencies/admin/agencies/{id}/approve/
Authorization: Bearer <admin_token>
```
→ `agency.is_approved = True`, `agency.approved_at = now`
→ All AGENCY users linked to this agency: `is_active = True`
→ Agency users can now log in

---

### 9.4 Create a Reservation with Tourists

**Step 1: Create Reservation (with tourists inline)**
```
POST /api/v1/reservations/client/reservations/
Authorization: Bearer <user_token>
{
  "reservation_number": "RES-2025-001",
  "currency": 1,
  "status": "DRAFT",
  "tour_package": null,
  "tourists": [
    {
      "first_name": "John",
      "last_name": "Doe",
      "sex": "MALE",
      "age_type": "ADULT",
      "passport_number": "AB123456",
      "nationality": "American",
      "birth_date": "1985-05-20",
      "passport_expiry_date": "2030-05-20"
    },
    {
      "first_name": "Jane",
      "last_name": "Doe",
      "sex": "FEMALE",
      "age_type": "ADULT",
      "passport_number": "CD789012"
    }
  ]
}
```
→ Reservation created with status `DRAFT`
→ Tourists created and linked to this reservation
→ If user is AGENCY role: `agency` is auto-set to their agency
→ If user is NORMAL role: `agency` is null

**Add tourists later (PATCH):**
```
PATCH /api/v1/reservations/client/reservations/{id}/
{
  "tourists": [
    { "id": 1, "passport_number": "AB123456-UPDATED" },   ← update existing
    { "first_name": "Child", "last_name": "Doe", "sex": "MALE", "age_type": "CHILD" }  ← add new
  ]
}
```

---

### 9.5 Add a Hotel Booking to a Reservation

**Prerequisites:** Reservation exists, HotelRoom exists, Tourists exist on the reservation

```
POST /api/v1/reservations/client/hotel-bookings/
Authorization: Bearer <user_token>
{
  "reservation": 1,
  "hotel_room": 5,
  "check_in_date": "2025-07-01",
  "check_out_date": "2025-07-07",
  "quantity": 1,
  "status": "PENDING",
  "selling_currency": 1,
  "price": 350.00,
  "agency_price": 300.00,
  "tourists": [1, 2],
  "remarks_for_hotel": "Late check-in expected"
}
```
→ Validates: dates within room window, availability, tourist capacity, tourists in same reservation
→ `hotel_room.availability_count -= 1` (atomically)

**Update to CONFIRMED:**
```
PATCH /api/v1/reservations/client/hotel-bookings/{id}/
{ "status": "CONFIRMED", "confirm_booking_number": "HTL-CONF-456" }
```

---

### 9.6 Add a Flight Ticket to a Reservation

One `FlightTicket` per tourist per flight:

```
POST /api/v1/reservations/client/flight-tickets/
Authorization: Bearer <user_token>
{
  "reservation": 1,
  "flight": 3,
  "tourist": 1,
  "ticket_number": "TK-123456789",
  "pnr_code": "ABCXYZ"
}
```

For multiple tourists on the same flight, make multiple POST requests (one per tourist):
```
POST /api/v1/reservations/client/flight-tickets/
{ "reservation": 1, "flight": 3, "tourist": 2, "ticket_number": "TK-987654321", "pnr_code": "ABCXYZ" }
```

---

### 9.7 Add an Excursion Booking to a Reservation

```
POST /api/v1/reservations/client/excursion-bookings/
Authorization: Bearer <user_token>
{
  "reservation": 1,
  "excursion": 2,
  "tourists": [1, 2],
  "tour_date": "2025-07-03",
  "pickup_time": "09:00:00"
}
```

---

### 9.8 Add a Transfer Service to a Reservation

**Option A: Linked to catalog Transfer (prices auto-filled):**
```
POST /api/v1/reservations/client/transfer-services/
Authorization: Bearer <user_token>
{
  "reservation": 1,
  "transfer": 4,
  "service_name": "Airport → Hotel Antalya",
  "service_date": "2025-07-01",
  "on_arrival": true,
  "on_departure": false,
  "from_location_type": "AIRPORT",
  "from_location_name": "Antalya Airport",
  "to_location_type": "HOTEL",
  "to_location_name": "Hotel Grand Antalya",
  "price": 50.00,
  "currency": 1,
  "passengers": [1, 2]
}
```

**Option B: Manual (no catalog link):**
```
POST /api/v1/reservations/client/transfer-services/
{
  "reservation": 1,
  "transfer": null,
  "service_name": "Custom Van Service",
  "service_date": "2025-07-07",
  "on_arrival": false,
  "on_departure": true,
  "from_location_type": "HOTEL",
  "from_location_name": "Hotel Grand Antalya",
  "to_location_type": "AIRPORT",
  "to_location_name": "Antalya Airport",
  "price": 60.00,
  "currency": 1,
  "passengers": [1, 2],
  "driver_note": "Flight at 22:00, pick up by 19:30"
}
```

---

### 9.9 Cancel a Hotel Booking

```
PATCH /api/v1/reservations/client/hotel-bookings/{id}/
{
  "status": "CANCELLED",
  "hotel_cancellation_number": "CANCEL-789"
}
```
→ `hotel_room.availability_count += quantity` (rooms restored automatically)

**Or delete the booking entirely:**
```
DELETE /api/v1/reservations/client/hotel-bookings/{id}/
```
→ If booking was not CANCELLED, rooms are restored before deletion

---

### 9.10 Cancel an Entire Reservation

```
PATCH /api/v1/reservations/client/reservations/{id}/
{ "status": "CANCELED" }
```
**Note:** Cancelling the Reservation record itself does NOT automatically cancel or restore the individual HotelBookings. You must cancel each HotelBooking manually if you want rooms to be restored.

**Recommended full cancellation flow:**
1. Cancel each HotelBooking: `PATCH hotel-bookings/{id}/ { "status": "CANCELLED" }`
2. Cancel the Reservation: `PATCH reservations/{id}/ { "status": "CANCELED" }`

---

### 9.11 Book a Standalone Excursion Service

Not linked to any Reservation — used for walk-in / direct excursion sales:

```
POST /api/v1/reservations/client/excursion-services/
Authorization: Bearer <user_token>
{
  "excursion_date": "2025-07-05",
  "excursion": 2,
  "is_combo": false,
  "pickup_point": "Hotel Lobby",
  "price": 45.00,
  "selling_currency": 1,
  "cost": 30.00,
  "cost_currency": 1,
  "cross_currency_rate": "1.0000000000",
  "is_paid": false,
  "note": "Group of 4 adults"
}
```
→ `system_date` is auto-set to now (read-only)

---

## 10. Price Visibility Rules

Every inventory item (HotelRoom, Flight, Transfer, Excursion, TourPackage) has three price tiers:

| Price Field | Who Sees It |
|-------------|-------------|
| `public_price` (or `price`) | Everyone (anonymous + normal users) |
| `agency_price` | Users with `can_access_agency_prices = True` (agency, staff, admin) |
| `cost_price` | Hidden from all client endpoints — admin/internal only |

**`can_access_agency_prices` is True when:**
- `user.is_superuser == True`, OR
- `user.is_staff == True`, OR
- `user.role in ['AGENCY', 'STAFF']`

Client serializers use `get_price_for_user(user)` which returns `agency_price` if user qualifies, otherwise `public_price`.

---

## 11. Hotel Room Availability Logic

`HotelRoom.availability_count` is the **total stock** of that room type.

When a HotelBooking is created (non-CANCELLED), `availability_count` is decremented atomically using:
```python
HotelRoom.objects.filter(pk=hotel_room_id).update(
    availability_count=F("availability_count") + delta
)
```

**Availability check during booking validation:**
```
available = hotel_room.availability_count
           - SUM(quantity of non-CANCELLED overlapping bookings)
```
If `requested_quantity > available` → validation error.

**The availability endpoint shows:**
- `total_count` — raw `availability_count` on the room record
- `confirmed_count` — quantity held by CONFIRMED bookings in the date range
- `pending_count` — quantity held by PENDING bookings in the date range
- `booked_count` — confirmed + pending
- `available_count` — `max(0, total_count - booked_count)`

---

## 12. Complete Entity-Relationship Summary

```
CustomUser ──FK──► Agency
                     │
                     └──FK──► Reservation ──FK──► Currency
                                   │          ──FK──► TourPackage
                                   │
                                   ├──◄FK── Tourist
                                   │
                                   ├──◄FK── HotelBooking ──FK──► HotelRoom ──FK──► Hotel
                                   │              └──M2M──► Tourist            └──M2M──► HotelFeature
                                   │                                            └──◄FK── HotelImage
                                   │
                                   ├──◄FK── FlightTicket ──FK──► Flight ──FK──► Currency
                                   │              └──FK──► Tourist
                                   │
                                   ├──◄FK── ExcursionBooking ──FK──► Excursion ──FK──► Currency
                                   │              └──M2M──► Tourist
                                   │
                                   └──◄FK── TransferService ──FK──► Transfer ──FK──► TransferProvider
                                                └──M2M──► Tourist       └──FK──► Currency

ExcursionService ──FK──► Excursion (standalone, no Reservation)

TourPackage ──M2M──► Flight
            ──M2M──► Hotel
            ──M2M──► Transfer
            ──M2M──► Excursion
            ──FK───► Currency

Invoice ──OneToOne──► Reservation

ExchangeRate ──FK──► Currency (base)
             ──FK──► Currency (target)
```

---

## 13. All API Endpoints Reference

### Auth
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/api/v1/auth/login/` | None | Get JWT access+refresh tokens |
| POST | `/api/v1/auth/refresh/` | None | Refresh access token |
| POST | `/api/v1/auth/register/` | None | Register normal user |

### Accounts
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/api/v1/accounts/admin/users/` | Admin | List all users |
| POST | `/api/v1/accounts/admin/users/` | Admin | Create user |
| GET | `/api/v1/accounts/admin/users/{id}/` | Admin | Get user |
| PUT/PATCH | `/api/v1/accounts/admin/users/{id}/` | Admin | Update user |
| DELETE | `/api/v1/accounts/admin/users/{id}/` | Admin | Delete user |
| GET | `/api/v1/accounts/client/users/{id}/` | Auth | Get own profile |
| PUT/PATCH | `/api/v1/accounts/client/users/{id}/` | Auth | Update own profile |

### Agencies
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/api/v1/agencies/admin/agencies/` | Admin | List all agencies |
| POST | `/api/v1/agencies/admin/agencies/` | Admin | Create agency |
| GET | `/api/v1/agencies/admin/agencies/{id}/` | Admin | Get agency |
| PUT/PATCH | `/api/v1/agencies/admin/agencies/{id}/` | Admin | Update agency |
| DELETE | `/api/v1/agencies/admin/agencies/{id}/` | Admin | Delete agency |
| POST | `/api/v1/agencies/admin/agencies/{id}/approve/` | Admin | Approve agency |
| GET | `/api/v1/agencies/client/agencies/` | None | List approved agencies |
| GET | `/api/v1/agencies/client/agencies/{id}/` | None | Get approved agency |
| POST | `/api/v1/agencies/client/register/` | None | Register new agency |

### Inventory — Hotels
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET/POST | `/api/v1/inventory/admin/hotels/` | Admin | List/Create hotels |
| GET/PUT/PATCH/DELETE | `/api/v1/inventory/admin/hotels/{id}/` | Admin | CRUD hotel |
| GET/POST | `/api/v1/inventory/admin/hotel-rooms/` | Admin | List/Create rooms |
| GET/PUT/PATCH/DELETE | `/api/v1/inventory/admin/hotel-rooms/{id}/` | Admin | CRUD room |
| GET | `/api/v1/inventory/admin/hotel-rooms/{id}/availability/` | Admin | Room availability |
| GET/POST | `/api/v1/inventory/admin/hotel-images/` | Admin | List/Upload images |
| GET/PUT/PATCH/DELETE | `/api/v1/inventory/admin/hotel-images/{id}/` | Admin | CRUD image |
| GET | `/api/v1/inventory/client/hotels/` | None | List hotels |
| GET | `/api/v1/inventory/client/hotels/{id}/` | None | Get hotel |
| GET | `/api/v1/inventory/client/hotel-rooms/` | None | List rooms |
| GET | `/api/v1/inventory/client/hotel-rooms/{id}/` | None | Get room |
| GET | `/api/v1/inventory/client/hotel-rooms/{id}/availability/` | None | Room availability |

### Inventory — Flights
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET/POST | `/api/v1/inventory/admin/flights/` | Admin | List/Create flights |
| GET/PUT/PATCH/DELETE | `/api/v1/inventory/admin/flights/{id}/` | Admin | CRUD flight |
| GET | `/api/v1/inventory/client/flights/` | None | List flights |
| GET | `/api/v1/inventory/client/flights/{id}/` | None | Get flight |

### Inventory — Transfers
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET/POST | `/api/v1/inventory/admin/transfer-providers/` | Admin | List/Create providers |
| GET/PUT/PATCH/DELETE | `/api/v1/inventory/admin/transfer-providers/{id}/` | Admin | CRUD provider |
| GET/POST | `/api/v1/inventory/admin/transfers/` | Admin | List/Create transfers |
| GET/PUT/PATCH/DELETE | `/api/v1/inventory/admin/transfers/{id}/` | Admin | CRUD transfer |
| GET | `/api/v1/inventory/client/transfers/` | None | List transfers |
| GET | `/api/v1/inventory/client/transfers/{id}/` | None | Get transfer |

### Inventory — Excursions
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET/POST | `/api/v1/inventory/admin/excursions/` | Admin | List/Create excursions |
| GET/PUT/PATCH/DELETE | `/api/v1/inventory/admin/excursions/{id}/` | Admin | CRUD excursion |
| GET | `/api/v1/inventory/client/excursions/` | None | List excursions |
| GET | `/api/v1/inventory/client/excursions/{id}/` | None | Get excursion |

### Inventory — Tour Packages
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET/POST | `/api/v1/inventory/admin/tour-packages/` | Admin | List/Create packages |
| GET/PUT/PATCH/DELETE | `/api/v1/inventory/admin/tour-packages/{id}/` | Admin | CRUD package |
| GET | `/api/v1/inventory/client/tour-packages/` | None | List packages |
| GET | `/api/v1/inventory/client/tour-packages/{id}/` | None | Get package |

### Reservations
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET/POST | `/api/v1/reservations/admin/reservations/` | Admin | List/Create reservations |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/admin/reservations/{id}/` | Admin | CRUD reservation |
| GET/POST | `/api/v1/reservations/admin/tourists/` | Admin | List/Create tourists |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/admin/tourists/{id}/` | Admin | CRUD tourist |
| GET/POST | `/api/v1/reservations/admin/hotel-bookings/` | Admin | List/Create hotel bookings |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/admin/hotel-bookings/{id}/` | Admin | CRUD hotel booking |
| GET/POST | `/api/v1/reservations/admin/flight-tickets/` | Admin | List/Create flight tickets |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/admin/flight-tickets/{id}/` | Admin | CRUD flight ticket |
| GET/POST | `/api/v1/reservations/admin/excursion-bookings/` | Admin | List/Create excursion bookings |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/admin/excursion-bookings/{id}/` | Admin | CRUD excursion booking |
| GET/POST | `/api/v1/reservations/admin/transfer-services/` | Admin | List/Create transfer services |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/admin/transfer-services/{id}/` | Admin | CRUD transfer service |
| GET/POST | `/api/v1/reservations/admin/excursion-services/` | Admin | List/Create standalone excursion services |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/admin/excursion-services/{id}/` | Admin | CRUD excursion service |
| GET/POST | `/api/v1/reservations/client/reservations/` | Auth | List/Create reservations |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/client/reservations/{id}/` | Auth | CRUD reservation |
| GET/POST | `/api/v1/reservations/client/tourists/` | Auth | List/Create tourists |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/client/tourists/{id}/` | Auth | CRUD tourist |
| GET/POST | `/api/v1/reservations/client/hotel-bookings/` | Auth | List/Create hotel bookings |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/client/hotel-bookings/{id}/` | Auth | CRUD hotel booking |
| GET/POST | `/api/v1/reservations/client/flight-tickets/` | Auth | List/Create flight tickets |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/client/flight-tickets/{id}/` | Auth | CRUD flight ticket |
| GET/POST | `/api/v1/reservations/client/excursion-bookings/` | Auth | List/Create excursion bookings |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/client/excursion-bookings/{id}/` | Auth | CRUD excursion booking |
| GET/POST | `/api/v1/reservations/client/transfer-services/` | Auth | List/Create transfer services |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/client/transfer-services/{id}/` | Auth | CRUD transfer service |
| GET/POST | `/api/v1/reservations/client/excursion-services/` | Auth | List/Create standalone excursion services |
| GET/PUT/PATCH/DELETE | `/api/v1/reservations/client/excursion-services/{id}/` | Auth | CRUD excursion service |

### Finance
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET/POST | `/api/v1/finance/admin/currencies/` | Admin | List/Create currencies |
| GET/PUT/PATCH/DELETE | `/api/v1/finance/admin/currencies/{id}/` | Admin | CRUD currency |
| GET/POST | `/api/v1/finance/admin/exchange-rates/` | Admin | List/Create rates |
| GET/PUT/PATCH/DELETE | `/api/v1/finance/admin/exchange-rates/{id}/` | Admin | CRUD rate |
| GET/POST | `/api/v1/finance/admin/invoices/` | Admin | List/Create invoices |
| GET/PUT/PATCH/DELETE | `/api/v1/finance/admin/invoices/{id}/` | Admin | CRUD invoice |
| GET | `/api/v1/finance/client/currencies/` | None | List active currencies |
| GET | `/api/v1/finance/client/exchange-rates/` | None | List exchange rates |
| GET | `/api/v1/finance/client/invoices/` | Auth | List invoices |
| GET | `/api/v1/finance/client/convert/` | None | Convert currency amount |

---

*End of document. This file covers every model, relationship, flow, validation rule, and API endpoint in the Jovira backend as of 2026-06-08.*
