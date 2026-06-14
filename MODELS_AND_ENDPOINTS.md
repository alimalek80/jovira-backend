# Jovira Backend — All Models, Views & Endpoints

> Complete reference for all Django apps: `accounts`, `agencies`, `inventory`, `reservations`, `finance`, `publicsite`.
> Generated: 2026-06-08

---

## Table of Contents

1. [Global Configuration](#1-global-configuration)
2. [App: accounts](#2-app-accounts)
   - [Models](#21-models)
   - [Serializers](#22-serializers)
   - [Views](#23-views)
   - [URLs / Endpoints](#24-urls--endpoints)
3. [App: agencies](#3-app-agencies)
   - [Models](#31-models)
   - [Serializers](#32-serializers)
   - [Views](#33-views)
   - [URLs / Endpoints](#34-urls--endpoints)
4. [App: inventory](#4-app-inventory)
   - [Models](#41-models)
   - [Serializers](#42-serializers)
   - [Views](#43-views)
   - [URLs / Endpoints](#44-urls--endpoints)
5. [App: reservations](#5-app-reservations)
   - [Models](#51-models)
   - [Serializers](#52-serializers)
   - [Views](#53-views)
   - [URLs / Endpoints](#54-urls--endpoints)
6. [App: finance](#6-app-finance)
   - [Models](#61-models)
   - [Serializers](#62-serializers)
   - [Views](#63-views)
   - [URLs / Endpoints](#64-urls--endpoints)
7. [App: publicsite](#7-app-publicsite)
   - [Models](#71-models)
   - [Serializers](#72-serializers)
   - [Views](#73-views)
   - [URLs / Endpoints](#74-urls--endpoints)
8. [Root URL Configuration](#8-root-url-configuration)
9. [Permission Classes Summary](#9-permission-classes-summary)
10. [Serializer Fields — Complete Reference](#10-serializer-fields--complete-reference)

---

## 1. Global Configuration

| Setting | Value |
|---------|-------|
| Framework | Django + Django REST Framework |
| Auth | JWT (`rest_framework_simplejwt`) — email-based login, no username |
| API docs | `drf_spectacular` → Swagger UI at `/api/schema/swagger-ui/` |
| Translations | `modeltranslation` — all translated fields have `_en`, `_tr`, `_ru` variants |
| Database | SQLite (`db.sqlite3`) |
| Media files | Served from `/media/` → `MEDIA_ROOT` |

**Installed custom apps:** `accounts`, `agencies`, `inventory`, `reservations`, `finance`, `publicsite`

---

## 2. App: accounts

### 2.1 Models

#### `CustomUser` — inherits `AbstractUser`

> File: `accounts/models.py`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | auto | |
| `email` | EmailField | unique, `USERNAME_FIELD` | No username — email is the login identifier |
| `first_name` | CharField | inherited | |
| `last_name` | CharField | inherited | |
| `phone_number` | CharField(20) | null, blank | |
| `role` | CharField(20) | choices | `NORMAL` / `AGENCY` / `STAFF` · default: `NORMAL` |
| `agency` | FK → `agencies.Agency` | null, blank, `SET_NULL` | Only set for AGENCY-role users |
| `is_active` | BooleanField | inherited | Set to `False` for agency users until agency is approved |
| `is_staff` | BooleanField | inherited | Django staff flag |
| `is_superuser` | BooleanField | inherited | Full permissions |
| `password` | CharField | inherited | Hashed |
| `date_joined` | DateTimeField | inherited | |

**Role choices:**

| Value | Label |
|-------|-------|
| `NORMAL` | Normal User |
| `AGENCY` | Agency |
| `STAFF` | Staff |

**Property `can_access_agency_prices`:**
Returns `True` when: `is_superuser=True` OR `is_staff=True` OR `role in {AGENCY, STAFF}`

**Meta:** `ordering = ("id",)`, `USERNAME_FIELD = "email"`, `REQUIRED_FIELDS = []`

---

### 2.2 Serializers

#### `RegisterSerializer`

> Used for public self-registration (`/api/v1/auth/register/`)

| Field | Writable | Notes |
|-------|----------|-------|
| `id` | read-only | |
| `email` | write | |
| `first_name` | write | |
| `last_name` | write | |
| `phone_number` | write | |
| `password` | write-only | min length 8 |
| `password2` | write-only | must match `password` |

**`create()` logic:** pops `password2`, sets `role = NORMAL`, `agency = None`, calls `create_user()`.

---

#### `AdminCustomUserSerializer`

> Used by admin endpoints — full field access

| Field | Writable |
|-------|----------|
| `id` | read-only |
| `email` | yes |
| `first_name` | yes |
| `last_name` | yes |
| `phone_number` | yes |
| `role` | yes |
| `agency` | yes |
| `is_active` | yes |
| `is_staff` | yes |
| `is_superuser` | yes |

---

#### `ClientCustomUserSerializer`

> Used by authenticated user self-service — restricted fields

| Field | Writable |
|-------|----------|
| `id` | read-only |
| `email` | yes |
| `first_name` | yes |
| `last_name` | yes |
| `phone_number` | yes |
| `role` | read-only |
| `agency` | read-only |
| `is_active` | read-only |

---

### 2.3 Views

#### `RegisterView`

| Attribute | Value |
|-----------|-------|
| Base class | `generics.CreateAPIView` |
| Serializer | `RegisterSerializer` |
| Permission | `AllowAny` |
| Methods | `POST` |

---

#### `AdminCustomUserViewSet`

| Attribute | Value |
|-----------|-------|
| Base class | `viewsets.ModelViewSet` |
| Serializer | `AdminCustomUserSerializer` |
| Permission | `IsAdminUser` |
| Queryset | `CustomUser.objects.all().order_by("id")` |
| Methods | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |

---

#### `ClientCustomUserViewSet`

| Attribute | Value |
|-----------|-------|
| Base class | `mixins.RetrieveModelMixin` + `mixins.UpdateModelMixin` + `GenericViewSet` |
| Serializer | `ClientCustomUserSerializer` |
| Permission | `IsAuthenticated` |
| Queryset | `CustomUser.objects.filter(id=request.user.id)` (own record only) |
| Methods | `GET`, `PUT`, `PATCH` |

---

### 2.4 URLs / Endpoints

> Prefix: `/api/v1/accounts/`

| Method | URL | View | Permission | Description |
|--------|-----|------|------------|-------------|
| `POST` | `/api/v1/auth/register/` | `RegisterView` | AllowAny | Register a new normal user |
| `GET` | `/api/v1/accounts/admin/users/` | `AdminCustomUserViewSet.list` | IsAdminUser | List all users |
| `POST` | `/api/v1/accounts/admin/users/` | `AdminCustomUserViewSet.create` | IsAdminUser | Create a user |
| `GET` | `/api/v1/accounts/admin/users/{id}/` | `AdminCustomUserViewSet.retrieve` | IsAdminUser | Get user by ID |
| `PUT` | `/api/v1/accounts/admin/users/{id}/` | `AdminCustomUserViewSet.update` | IsAdminUser | Full update user |
| `PATCH` | `/api/v1/accounts/admin/users/{id}/` | `AdminCustomUserViewSet.partial_update` | IsAdminUser | Partial update user |
| `DELETE` | `/api/v1/accounts/admin/users/{id}/` | `AdminCustomUserViewSet.destroy` | IsAdminUser | Delete user |
| `GET` | `/api/v1/accounts/client/users/{id}/` | `ClientCustomUserViewSet.retrieve` | IsAuthenticated | Get own profile |
| `PUT` | `/api/v1/accounts/client/users/{id}/` | `ClientCustomUserViewSet.update` | IsAuthenticated | Full update own profile |
| `PATCH` | `/api/v1/accounts/client/users/{id}/` | `ClientCustomUserViewSet.partial_update` | IsAuthenticated | Partial update own profile |

---

## 3. App: agencies

### 3.1 Models

#### `Agency`

> File: `agencies/models.py`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | auto | |
| `name` | CharField(255) | required | Agency display name |
| `agency_type` | CharField(100) | required | e.g. "Tour Operator" |
| `contact_person` | CharField(255) | required | Primary contact name |
| `email` | EmailField(255) | null, blank | Agency contact email |
| `phone` | CharField(50) | null, blank | |
| `mobile_phone` | CharField(50) | null, blank | |
| `skype_id` | CharField(100) | null, blank | |
| `icq` | CharField(50) | null, blank | |
| `is_approved` | BooleanField | default `False` | Must be set to True by admin before agency users can log in |
| `approved_at` | DateTimeField | null, blank | Set only on first approval |

**Method `approve()`:** sets `is_approved=True`, sets `approved_at` to `now()` (only on first call), saves only those two fields.

**Meta:** `ordering = ("name",)`

---

### 3.2 Serializers

#### `AdminAgencySerializer`

| Field | Writable | Notes |
|-------|----------|-------|
| `id` | read-only | |
| `name` | yes | |
| `agency_type` | yes | |
| `contact_person` | yes | |
| `email` | yes | |
| `phone` | yes | |
| `mobile_phone` | yes | |
| `skype_id` | yes | |
| `icq` | yes | |
| `is_approved` | yes | Admin can toggle manually |
| `approved_at` | yes | |

---

#### `ClientAgencySerializer`

Same fields as Admin except `is_approved` and `approved_at` are **excluded** (not shown to clients).

| Included fields | `id`, `name`, `agency_type`, `contact_person`, `email`, `phone`, `mobile_phone`, `skype_id`, `icq` |

---

#### `AgencyRegisterSerializer`

> Used for the public agency registration endpoint. Creates both the Agency and a linked CustomUser in one atomic transaction.

| Field | Source | Notes |
|-------|--------|-------|
| `id` | Agency | read-only |
| `name` | Agency | |
| `agency_type` | Agency | |
| `contact_person` | Agency | |
| `email` | Agency | |
| `phone` | Agency | |
| `mobile_phone` | Agency | |
| `skype_id` | Agency | |
| `icq` | Agency | |
| `is_approved` | Agency | read-only |
| `approved_at` | Agency | read-only |
| `account_email` | Extra (write-only) | Email for the new user account |
| `account_first_name` | Extra (write-only) | optional |
| `account_last_name` | Extra (write-only) | optional |
| `account_phone_number` | Extra (write-only) | optional |
| `password` | Extra (write-only) | min 8 chars |
| `password2` | Extra (write-only) | must match password |

**`create()` logic (atomic transaction):**
1. Creates `Agency` record (`is_approved=False`)
2. Creates `CustomUser` with `role=AGENCY`, `is_active=False`, linked to the new agency

---

### 3.3 Views

#### `AdminAgencyViewSet`

| Attribute | Value |
|-----------|-------|
| Base class | `viewsets.ModelViewSet` |
| Serializer | `AdminAgencySerializer` |
| Permission | `IsAdminUser` |
| Queryset | `Agency.objects.all().order_by("name")` |
| Methods | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` + custom `approve` action |

**Custom action `approve` (`POST /agencies/{id}/approve/`):**
- Calls `agency.approve()`
- Sets `is_active=True` on all `CustomUser` records linked to this agency with `role=AGENCY`

---

#### `ClientAgencyViewSet`

| Attribute | Value |
|-----------|-------|
| Base class | `viewsets.ReadOnlyModelViewSet` |
| Serializer | `ClientAgencySerializer` |
| Permission | `AllowAny` |
| Queryset | `Agency.objects.filter(is_approved=True).order_by("name")` |
| Methods | `GET` (list + retrieve only) |

---

#### `AgencyRegisterView`

| Attribute | Value |
|-----------|-------|
| Base class | `generics.CreateAPIView` |
| Serializer | `AgencyRegisterSerializer` |
| Permission | `AllowAny` |
| Methods | `POST` |

---

### 3.4 URLs / Endpoints

> Prefix: `/api/v1/agencies/`

| Method | URL | View | Permission | Description |
|--------|-----|------|------------|-------------|
| `GET` | `/api/v1/agencies/admin/agencies/` | `AdminAgencyViewSet.list` | IsAdminUser | List all agencies |
| `POST` | `/api/v1/agencies/admin/agencies/` | `AdminAgencyViewSet.create` | IsAdminUser | Create agency |
| `GET` | `/api/v1/agencies/admin/agencies/{id}/` | `AdminAgencyViewSet.retrieve` | IsAdminUser | Get agency |
| `PUT` | `/api/v1/agencies/admin/agencies/{id}/` | `AdminAgencyViewSet.update` | IsAdminUser | Full update agency |
| `PATCH` | `/api/v1/agencies/admin/agencies/{id}/` | `AdminAgencyViewSet.partial_update` | IsAdminUser | Partial update agency |
| `DELETE` | `/api/v1/agencies/admin/agencies/{id}/` | `AdminAgencyViewSet.destroy` | IsAdminUser | Delete agency |
| `POST` | `/api/v1/agencies/admin/agencies/{id}/approve/` | `AdminAgencyViewSet.approve` | IsAdminUser | Approve agency + activate its users |
| `GET` | `/api/v1/agencies/client/agencies/` | `ClientAgencyViewSet.list` | AllowAny | List approved agencies |
| `GET` | `/api/v1/agencies/client/agencies/{id}/` | `ClientAgencyViewSet.retrieve` | AllowAny | Get approved agency |
| `POST` | `/api/v1/agencies/client/register/` | `AgencyRegisterView` | AllowAny | Register new agency + user |

---

## 4. App: inventory

### 4.1 Models

#### `HotelFeature`

| Field | Type | Notes |
|-------|------|-------|
| `id` | AutoField (PK) | |
| `name` | CharField(100) | + `name_en`, `name_tr`, `name_ru` (modeltranslation) |

**Meta:** `ordering = ("name",)`

---

#### `Hotel`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `name` | CharField(255) | | + `name_en`, `name_tr`, `name_ru` |
| `city` | CharField(120) | | + `city_en`, `city_tr`, `city_ru` |
| `stars` | IntegerField | | 1–5 |
| `description` | TextField | null, blank | + `description_en`, `description_tr`, `description_ru` |
| `main_image` | ImageField | blank, null | Upload to `hotels/main/` |
| `features` | M2M → `HotelFeature` | blank | Amenities tags |

**Reverse relations:** `rooms` (from HotelRoom), `gallery_images` (from HotelImage), `tour_packages` (from TourPackage M2M)

**Meta:** `ordering = ("name",)`

---

#### `HotelImage`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `hotel` | FK → `Hotel` | CASCADE | |
| `image` | ImageField | | Upload to `hotels/gallery/` |
| `alt_text` | CharField(255) | blank | |
| `order` | PositiveIntegerField | default 0 | Display order |

**Meta:** `ordering = ("order", "id")`

---

#### `HotelRoom`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `hotel` | FK → `Hotel` | CASCADE | |
| `room_type` | CharField(20) | choices | `SINGLE`, `DOUBLE`, `TRIPLE`, `FAMILY`, `SUITE` |
| `board_type` | CharField(10) | choices | `RO`, `BB`, `HB`, `FB`, `ALL`, `UALL` |
| `date_from` | DateField | | Start of availability window |
| `date_to` | DateField | | End of availability window |
| `availability_count` | PositiveIntegerField | default 0 | Total rooms in stock |
| `currency` | FK → `finance.Currency` | PROTECT | |
| `public_price` | DecimalField(12,2) | | Shown to all users |
| `agency_price` | DecimalField(12,2) | null, blank | Shown to agency/staff/admin |
| `cost_price` | DecimalField(12,2) | null, blank | Internal only — never shown to client |
| `note` | TextField | blank | |

**Room type capacity map:** SINGLE=1, DOUBLE=2, TRIPLE=3, FAMILY=4, SUITE=4

**Method `get_price_for_user(user)`:** returns `agency_price` if `can_access_agency_prices`, else `public_price`

**Meta:** `ordering = ("hotel", "date_from", "room_type")`

---

#### `Flight`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `flight_number` | CharField(50) | | e.g. `TK101` |
| `airline` | CharField(120) | | |
| `origin` | CharField(120) | | + `origin_en`, `origin_tr`, `origin_ru` |
| `destination` | CharField(120) | | + `destination_en`, `destination_tr`, `destination_ru` |
| `departure_time` | DateTimeField | | |
| `arrival_time` | DateTimeField | | |
| `currency` | FK → `finance.Currency` | PROTECT, null, blank | |
| `price` | DecimalField(12,2) | null, blank | Public price |
| `agency_price` | DecimalField(12,2) | null, blank | Agency/staff/admin price |
| `cost_price` | DecimalField(12,2) | null, blank | Internal only |

**Method `get_price_for_user(user)`:** returns `agency_price` if `can_access_agency_prices`, else `price`

**Meta:** `ordering = ("-departure_time")`

---

#### `TransferProvider`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `name` | CharField(255) | | |
| `provider_type` | CharField(20) | choices | `COMPANY` / `INDIVIDUAL` · default `COMPANY` |
| `contact_person` | CharField(255) | blank | |
| `phone` | CharField(50) | blank | |
| `email` | EmailField | blank | |
| `notes` | TextField | blank | |

**Meta:** `ordering = ("name",)`

---

#### `Transfer`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `provider` | FK → `TransferProvider` | PROTECT | |
| `name` | CharField(255) | | + `name_en`, `name_tr`, `name_ru` |
| `from_location` | CharField(255) | | + `from_location_en`, `from_location_tr`, `from_location_ru` |
| `to_location` | CharField(255) | | + `to_location_en`, `to_location_tr`, `to_location_ru` |
| `vehicle_type` | CharField(100) | blank | + `vehicle_type_en`, `vehicle_type_tr`, `vehicle_type_ru` |
| `capacity` | PositiveIntegerField | null, blank | Max passengers |
| `currency` | FK → `finance.Currency` | PROTECT, null, blank | |
| `public_price` | DecimalField(12,2) | null, blank | |
| `agency_price` | DecimalField(12,2) | null, blank | |
| `cost_price` | DecimalField(12,2) | null, blank | Internal only |

**Method `get_price_for_user(user)`:** returns `agency_price` if `can_access_agency_prices`, else `public_price`

**Meta:** `ordering = ("name",)`

---

#### `Excursion`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `name` | CharField(255) | | + `name_en`, `name_tr`, `name_ru` |
| `city` | CharField(120) | | + `city_en`, `city_tr`, `city_ru` |
| `duration_hours` | DecimalField(5,2) | | e.g. `3.50` |
| `currency` | FK → `finance.Currency` | PROTECT, null, blank | |
| `public_price` | DecimalField(12,2) | null, blank | |
| `agency_price` | DecimalField(12,2) | null, blank | |
| `cost_price` | DecimalField(12,2) | null, blank | Internal only |

**Method `get_price_for_user(user)`:** returns `agency_price` if `can_access_agency_prices`, else `public_price`

**Meta:** `ordering = ("name",)`

---

#### `TourPackage`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `name` | CharField(255) | | + `name_en`, `name_tr`, `name_ru` |
| `destination` | CharField(120) | | + `destination_en`, `destination_tr`, `destination_ru` |
| `days` | IntegerField | | |
| `nights` | IntegerField | | |
| `currency` | FK → `finance.Currency` | PROTECT, null, blank | Package base currency |
| `public_price` | DecimalField(12,2) | null, blank | |
| `agency_price` | DecimalField(12,2) | null, blank | |
| `cost_price` | DecimalField(12,2) | null, blank | Internal only · must be ≥ component cost floor |
| `flights` | M2M → `Flight` | blank | |
| `hotels` | M2M → `Hotel` | blank | |
| `transfers` | M2M → `Transfer` | blank | |
| `excursions` | M2M → `Excursion` | blank | |

**Method `calculate_minimum_cost_floor()`:** sums all linked component `cost_price` values, converted to the package currency via `ExchangeRate`.

**`clean()` validation:**
- `cost_price` ≥ component floor
- `agency_price` ≥ component floor
- `public_price` ≥ component floor
- `public_price` ≥ `agency_price`

**Method `get_price_for_user(user)`:** returns `agency_price` or `public_price`

**Meta:** `ordering = ("name",)`

---

### 4.2 Serializers

#### `HotelFeatureSerializer`
Fields: `id`, `name`, `name_en`, `name_tr`, `name_ru`

#### `HotelImageSerializer`
Fields: `id`, `hotel`, `image`, `alt_text`, `order`

#### `HotelRoomSerializer` (admin)
Fields: `id`, `hotel`, `room_type`, `board_type`, `date_from`, `date_to`, `availability_count`, `currency`, `public_price`, `agency_price`, `cost_price`, `note`

#### `ClientHotelRoomSerializer`
Fields: `id`, `hotel`, `room_type`, `board_type`, `date_from`, `date_to`, `availability_count`, `currency`, `price` (computed), `note`
— `price` calls `get_price_for_user(user)` — hides `agency_price` and `cost_price`

#### `HotelSerializer` (admin)
Fields: all Hotel fields + translations, `features` (nested), `gallery_images` (nested), `rooms` (nested)

#### `ClientHotelSerializer`
Same fields as `HotelSerializer` but `rooms` uses `ClientHotelRoomSerializer`

#### `FlightSerializer` (admin)
Fields: `id`, `flight_number`, `airline`, `origin` (+translations), `destination` (+translations), `departure_time`, `arrival_time`, `currency`, `price`, `agency_price`, `cost_price`

#### `ClientFlightSerializer`
Fields: same minus `agency_price`, `cost_price` — `price` is computed via `get_price_for_user`

#### `TourPackageSerializer` (admin / staff)
Fields: `id`, `name` (+translations), `destination` (+translations), `days`, `nights`, `currency`, `public_price`, `agency_price`, `cost_price`, `flights`, `hotels`, `transfers`, `excursions`, `minimum_cost_floor` (read-only, computed)
— Validates cost floor rules on save

#### `ClientTourPackageSerializer`
Fields: `id`, `name` (+translations), `destination` (+translations), `days`, `nights`, `currency`, `price` (computed via `get_price_for_user`)

#### `ExcursionSerializer` (admin)
Fields: `id`, `name` (+translations), `city` (+translations), `duration_hours`, `currency`, `public_price`, `agency_price`, `cost_price`

#### `ClientExcursionSerializer`
Fields: same minus `agency_price`, `cost_price` — `price` computed

#### `TransferProviderSerializer`
Fields: `id`, `name`, `provider_type`, `contact_person`, `phone`, `email`, `notes`

#### `TransferSerializer` (admin)
Fields: `id`, `provider`, `name` (+translations), `from_location` (+translations), `to_location` (+translations), `vehicle_type` (+translations), `capacity`, `currency`, `public_price`, `agency_price`, `cost_price`

#### `ClientTransferSerializer`
Fields: same minus `agency_price`, `cost_price` — `price` computed

---

### 4.3 Views

#### `AdminHotelViewSet`
| Attribute | Value |
|-----------|-------|
| Base | `ModelViewSet` |
| Serializer | `HotelSerializer` |
| Permission | `IsAdminUser` |
| Queryset | `Hotel.objects.all().order_by("name")` |

#### `AdminHotelRoomViewSet`
| Attribute | Value |
|-----------|-------|
| Base | `ModelViewSet` |
| Serializer | `HotelRoomSerializer` |
| Permission | `IsAdminUser` |
| Queryset | `HotelRoom.objects.select_related("hotel", "currency").order_by(...)` |
| Filter | `?hotel={id}` query param |
| Extra action | `GET /{id}/availability/?check_in=YYYY-MM-DD&check_out=YYYY-MM-DD` — returns `{total_count, confirmed_count, pending_count, booked_count, available_count}` |

#### `AdminHotelImageViewSet`
| Attribute | Value |
|-----------|-------|
| Base | `ModelViewSet` |
| Serializer | `HotelImageSerializer` |
| Permission | `IsAdminUser` |
| Parsers | `MultiPartParser`, `FormParser` (file uploads) |
| Filter | `?hotel={id}` query param |

#### `ClientHotelViewSet`
| Permission | `AllowAny` | `ReadOnlyModelViewSet` | Serializer: `ClientHotelSerializer` |

#### `ClientHotelRoomViewSet`
| Permission | `AllowAny` | `ReadOnlyModelViewSet` | Serializer: `ClientHotelRoomSerializer` |
| Filter | `?hotel={id}` |
| Extra action | `GET /{id}/availability/?check_in=&check_out=` |

#### `AdminFlightViewSet`
| Permission | `IsAdminUser` | `ModelViewSet` | Serializer: `FlightSerializer` |

#### `ClientFlightViewSet`
| Permission | `AllowAny` | `ReadOnlyModelViewSet` | Serializer: `ClientFlightSerializer` |

#### `AdminTourPackageViewSet`
| Permission | `IsAdminOrStaffRole` (admin OR role=STAFF) | `ModelViewSet` | Serializer: `TourPackageSerializer` |
| Extra action | `GET /{id}/hotels/` — returns list of hotels linked to this package |

#### `ClientTourPackageViewSet`
| Permission | `AllowAny` | `ReadOnlyModelViewSet` | Serializer: `ClientTourPackageSerializer` |
| Extra action | `GET /{id}/hotels/` |

#### `AdminExcursionViewSet`
| Permission | `IsAdminUser` | `ModelViewSet` | Serializer: `ExcursionSerializer` |

#### `ClientExcursionViewSet`
| Permission | `AllowAny` | `ReadOnlyModelViewSet` | Serializer: `ClientExcursionSerializer` |

#### `AdminTransferProviderViewSet`
| Permission | `IsAdminUser` | `ModelViewSet` | Serializer: `TransferProviderSerializer` |

#### `AdminTransferViewSet`
| Permission | `IsAdminUser` | `ModelViewSet` | Serializer: `TransferSerializer` |

#### `ClientTransferViewSet`
| Permission | `IsAuthenticated` | `ReadOnlyModelViewSet` | Serializer: `ClientTransferSerializer` |

---

### 4.4 URLs / Endpoints

> Prefix: `/api/v1/inventory/`

#### Admin endpoints

| Method | URL | View | Description |
|--------|-----|------|-------------|
| `GET` | `.../admin/hotels/` | `AdminHotelViewSet.list` | List hotels |
| `POST` | `.../admin/hotels/` | `AdminHotelViewSet.create` | Create hotel |
| `GET` | `.../admin/hotels/{id}/` | `.retrieve` | Get hotel |
| `PUT` | `.../admin/hotels/{id}/` | `.update` | Full update hotel |
| `PATCH` | `.../admin/hotels/{id}/` | `.partial_update` | Partial update hotel |
| `DELETE` | `.../admin/hotels/{id}/` | `.destroy` | Delete hotel |
| `GET` | `.../admin/hotel-rooms/` | `AdminHotelRoomViewSet.list` | List rooms (`?hotel=id`) |
| `POST` | `.../admin/hotel-rooms/` | `.create` | Create room |
| `GET` | `.../admin/hotel-rooms/{id}/` | `.retrieve` | Get room |
| `PUT` | `.../admin/hotel-rooms/{id}/` | `.update` | Full update room |
| `PATCH` | `.../admin/hotel-rooms/{id}/` | `.partial_update` | Partial update room |
| `DELETE` | `.../admin/hotel-rooms/{id}/` | `.destroy` | Delete room |
| `GET` | `.../admin/hotel-rooms/{id}/availability/` | `.availability` | Room availability for date range |
| `GET` | `.../admin/hotel-images/` | `AdminHotelImageViewSet.list` | List images (`?hotel=id`) |
| `POST` | `.../admin/hotel-images/` | `.create` | Upload image (multipart) |
| `GET` | `.../admin/hotel-images/{id}/` | `.retrieve` | Get image |
| `PUT` | `.../admin/hotel-images/{id}/` | `.update` | Update image |
| `PATCH` | `.../admin/hotel-images/{id}/` | `.partial_update` | Partial update image |
| `DELETE` | `.../admin/hotel-images/{id}/` | `.destroy` | Delete image |
| `GET` | `.../admin/flights/` | `AdminFlightViewSet.list` | List flights |
| `POST` | `.../admin/flights/` | `.create` | Create flight |
| `GET` | `.../admin/flights/{id}/` | `.retrieve` | Get flight |
| `PUT` | `.../admin/flights/{id}/` | `.update` | Update flight |
| `PATCH` | `.../admin/flights/{id}/` | `.partial_update` | Partial update flight |
| `DELETE` | `.../admin/flights/{id}/` | `.destroy` | Delete flight |
| `GET` | `.../admin/tour-packages/` | `AdminTourPackageViewSet.list` | List tour packages |
| `POST` | `.../admin/tour-packages/` | `.create` | Create tour package |
| `GET` | `.../admin/tour-packages/{id}/` | `.retrieve` | Get tour package |
| `PUT` | `.../admin/tour-packages/{id}/` | `.update` | Update tour package |
| `PATCH` | `.../admin/tour-packages/{id}/` | `.partial_update` | Partial update |
| `DELETE` | `.../admin/tour-packages/{id}/` | `.destroy` | Delete tour package |
| `GET` | `.../admin/tour-packages/{id}/hotels/` | `.hotels` | Hotels in this package |
| `GET` | `.../admin/excursions/` | `AdminExcursionViewSet.list` | List excursions |
| `POST` | `.../admin/excursions/` | `.create` | Create excursion |
| `GET` | `.../admin/excursions/{id}/` | `.retrieve` | Get excursion |
| `PUT` | `.../admin/excursions/{id}/` | `.update` | Update excursion |
| `PATCH` | `.../admin/excursions/{id}/` | `.partial_update` | Partial update |
| `DELETE` | `.../admin/excursions/{id}/` | `.destroy` | Delete excursion |
| `GET` | `.../admin/transfer-providers/` | `AdminTransferProviderViewSet.list` | List providers |
| `POST` | `.../admin/transfer-providers/` | `.create` | Create provider |
| `GET` | `.../admin/transfer-providers/{id}/` | `.retrieve` | Get provider |
| `PUT` | `.../admin/transfer-providers/{id}/` | `.update` | Update provider |
| `PATCH` | `.../admin/transfer-providers/{id}/` | `.partial_update` | Partial update |
| `DELETE` | `.../admin/transfer-providers/{id}/` | `.destroy` | Delete provider |
| `GET` | `.../admin/transfers/` | `AdminTransferViewSet.list` | List transfers |
| `POST` | `.../admin/transfers/` | `.create` | Create transfer |
| `GET` | `.../admin/transfers/{id}/` | `.retrieve` | Get transfer |
| `PUT` | `.../admin/transfers/{id}/` | `.update` | Update transfer |
| `PATCH` | `.../admin/transfers/{id}/` | `.partial_update` | Partial update |
| `DELETE` | `.../admin/transfers/{id}/` | `.destroy` | Delete transfer |

#### Client endpoints (read-only or public)

| Method | URL | Permission | Description |
|--------|-----|------------|-------------|
| `GET` | `.../client/hotels/` | AllowAny | List hotels |
| `GET` | `.../client/hotels/{id}/` | AllowAny | Get hotel |
| `GET` | `.../client/hotel-rooms/` | AllowAny | List rooms (`?hotel=id`) |
| `GET` | `.../client/hotel-rooms/{id}/` | AllowAny | Get room |
| `GET` | `.../client/hotel-rooms/{id}/availability/` | AllowAny | Room availability |
| `GET` | `.../client/flights/` | AllowAny | List flights |
| `GET` | `.../client/flights/{id}/` | AllowAny | Get flight |
| `GET` | `.../client/tour-packages/` | AllowAny | List packages |
| `GET` | `.../client/tour-packages/{id}/` | AllowAny | Get package |
| `GET` | `.../client/tour-packages/{id}/hotels/` | AllowAny | Hotels in package |
| `GET` | `.../client/excursions/` | AllowAny | List excursions |
| `GET` | `.../client/excursions/{id}/` | AllowAny | Get excursion |
| `GET` | `.../client/transfers/` | IsAuthenticated | List transfers |
| `GET` | `.../client/transfers/{id}/` | IsAuthenticated | Get transfer |

---

## 5. App: reservations

### 5.1 Models

#### `Reservation`

> File: `reservations/models.py`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `reservation_number` | CharField(100) | unique | Must be supplied on creation |
| `created_at` | DateTimeField | auto_now_add | Read-only |
| `currency` | FK → `finance.Currency` | PROTECT | Billing currency for this reservation |
| `status` | CharField(20) | choices, default `DRAFT` | `DRAFT`, `ON_PROCESS`, `CONFIRMED`, `CANCELED` |
| `agency` | FK → `agencies.Agency` | null, blank, `SET_NULL` | Auto-assigned for AGENCY-role users |
| `tour_package` | FK → `inventory.TourPackage` | null, blank, `SET_NULL` | Optional package link |

**Reverse relations:** `tourists`, `hotel_bookings`, `flight_tickets`, `excursion_bookings`, `transfer_services` (all FK from child models), `invoice` (OneToOne from finance.Invoice)

**Status choices:** `DRAFT` → `ON_PROCESS` → `CONFIRMED` → `CANCELED` (can go to CANCELED from any state)

**Meta:** `ordering = ("-created_at",)`

---

#### `Tourist`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `reservation` | FK → `Reservation` | CASCADE | |
| `first_name` | CharField(150) | | |
| `last_name` | CharField(150) | | |
| `sex` | CharField(10) | choices | `MALE`, `FEMALE` |
| `age_type` | CharField(10) | choices | `ADULT`, `CHILD`, `INFANT` |
| `passport_number` | CharField(50) | blank | |
| `nationality` | CharField(100) | blank | |
| `birth_date` | DateField | null, blank | |
| `passport_expiry_date` | DateField | null, blank | |

**Meta:** `ordering = ("id",)`

---

#### `HotelBooking`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `reservation` | FK → `Reservation` | CASCADE | |
| `hotel_room` | FK → `inventory.HotelRoom` | PROTECT | |
| `check_in_date` | DateField | | |
| `check_out_date` | DateField | | Must be after check_in_date |
| `quantity` | PositiveIntegerField | default 1 | Number of rooms |
| `status` | CharField(20) | choices, default `PENDING` | `PENDING`, `CONFIRMED`, `CANCELLED` |
| `tourists` | M2M → `Tourist` | blank | Guests assigned to these rooms |
| `selling_currency` | FK → `finance.Currency` | PROTECT, null, blank | |
| `price` | DecimalField(12,2) | null, blank | |
| `agency_price` | DecimalField(12,2) | null, blank | |
| `cost_currency` | FK → `finance.Currency` | PROTECT, null, blank | |
| `cost` | DecimalField(12,2) | null, blank | |
| `cross_currency_rate` | DecimalField(15,10) | default 1.0 | |
| `confirm_booking_number` | CharField(50) | blank | Supplier confirmation |
| `agent_confirmation_number` | CharField(50) | blank | Agent's own reference |
| `hotel_cancellation_number` | CharField(50) | blank | Used on cancellation |
| `internal_note` | TextField | blank | Private |
| `remarks_for_hotel` | TextField | blank | Shown to hotel |
| `is_paid` | BooleanField | default False | |

**Meta:** `ordering = ("check_in_date",)`

**Availability side-effect (managed in view `perform_create/update/destroy`):**
- Non-CANCELLED create → `availability_count -= quantity`
- Delete non-CANCELLED → `availability_count += quantity`
- Status change to CANCELLED → restores rooms
- Status change from CANCELLED → deducts rooms
- Quantity change → adjusts difference
- Room change → restores old room, deducts new room

---

#### `FlightTicket`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `reservation` | FK → `Reservation` | CASCADE | |
| `flight` | FK → `inventory.Flight` | PROTECT | |
| `tourist` | FK → `Tourist` | CASCADE | One ticket = one person |
| `ticket_number` | CharField(100) | blank | Airline ticket number |
| `pnr_code` | CharField(50) | blank | Booking reference code |

**Meta:** `ordering = ("id",)`

---

#### `ExcursionBooking`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `reservation` | FK → `Reservation` | CASCADE | |
| `excursion` | FK → `inventory.Excursion` | PROTECT | |
| `tourists` | M2M → `Tourist` | | All tourists on this excursion |
| `tour_date` | DateField | | Date of excursion |
| `pickup_time` | TimeField | null, blank | |

**Meta:** `ordering = ("tour_date",)`

---

#### `TransferService`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `reservation` | FK → `Reservation` | CASCADE | |
| `transfer` | FK → `inventory.Transfer` | null, blank, `SET_NULL` | Optional catalog link |
| `tour_package` | FK → `inventory.TourPackage` | null, blank, `SET_NULL` | |
| `service_name` | CharField(255) | | Display name |
| `service_date` | DateField | | |
| `on_arrival` | BooleanField | default False | |
| `on_departure` | BooleanField | default False | |
| `from_location_type` | CharField(20) | choices | `AIRPORT`, `TERMINAL`, `HOTEL` |
| `from_location_name` | CharField(255) | | |
| `to_location_type` | CharField(20) | choices | `AIRPORT`, `TERMINAL`, `HOTEL` |
| `to_location_name` | CharField(255) | | |
| `price` | DecimalField(12,2) | | Public/selling price |
| `agency_price` | DecimalField(12,2) | null, blank | |
| `currency` | FK → `finance.Currency` | PROTECT | |
| `passengers` | M2M → `Tourist` | | |
| `external_note` | TextField | blank | Visible externally |
| `driver_note` | TextField | blank | For the driver |

**DB constraint:** `CHECK (on_arrival = TRUE OR on_departure = TRUE)` — at least one direction must be true.

**Meta:** `ordering = ("service_date", "id")`

---

#### `ExcursionService` (Standalone — no Reservation link)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `system_date` | DateTimeField | auto_now_add | Auto, read-only |
| `excursion_date` | DateField | | |
| `excursion` | FK → `inventory.Excursion` | PROTECT | |
| `is_combo` | BooleanField | default False | Combo excursion flag |
| `pickup_point` | CharField(255) | null, blank | |
| `price` | DecimalField(10,2) | default 0 | |
| `selling_currency` | FK → `finance.Currency` | PROTECT | |
| `cost` | DecimalField(10,2) | default 0 | |
| `cost_currency` | FK → `finance.Currency` | PROTECT | |
| `cross_currency_rate` | DecimalField(15,10) | default 1.0 | |
| `is_paid` | BooleanField | default False | |
| `confirm_booking_number` | CharField(50) | null, blank | |
| `agent_confirmation_number` | CharField(50) | null, blank | |
| `note` | TextField | null, blank | |

**Meta:** `ordering = ("-excursion_date",)`

---

### 5.2 Serializers

#### `TouristSerializer`

Fields: `id` (optional on write), `reservation` (optional), `first_name`, `last_name`, `sex`, `age_type`, `passport_number`, `nationality`, `birth_date`, `passport_expiry_date`

---

#### `HotelBookingSerializer`

Fields: `id`, `reservation`, `hotel_room`, `check_in_date`, `check_out_date`, `quantity`, `status`, `selling_currency`, `price`, `agency_price`, `cost_currency`, `cost`, `cross_currency_rate`, `confirm_booking_number`, `agent_confirmation_number`, `hotel_cancellation_number`, `internal_note`, `remarks_for_hotel`, `is_paid`, `tourists`

**Validation (`validate()`):**
- All tourists must belong to the same reservation
- Tourist count must not exceed `capacity_per_room × quantity`
- `check_out_date` must be after `check_in_date`
- Dates must fall within the room's `date_from`–`date_to` window
- Requested `quantity` must not exceed available rooms (overlapping non-CANCELLED bookings excluded)

---

#### `FlightTicketSerializer`

Fields: `id`, `reservation`, `flight`, `tourist`, `ticket_number`, `pnr_code`

---

#### `ExcursionBookingSerializer`

Fields: `id`, `reservation`, `excursion`, `tourists`, `tour_date`, `pickup_time`

---

#### `TransferServiceSerializer`

Fields: `id`, `reservation`, `transfer`, `tour_package`, `service_name`, `service_date`, `on_arrival`, `on_departure`, `from_location_type`, `from_location_name`, `to_location_type`, `to_location_name`, `price`, `agency_price`, `currency`, `passengers`, `external_note`, `driver_note`

**Validation:**
- At least one of `on_arrival` / `on_departure` must be True
- If reservation has a `tour_package`, the `tour_package` field here must match it
- All passengers must belong to the same reservation

---

#### `ExcursionServiceSerializer`

Fields: `id`, `system_date` (read-only), `excursion_date`, `excursion`, `is_combo`, `pickup_point`, `price`, `selling_currency`, `cost`, `cost_currency`, `cross_currency_rate`, `is_paid`, `confirm_booking_number`, `agent_confirmation_number`, `note`

---

#### `ReservationSerializer`

Fields: `id`, `reservation_number`, `created_at` (read-only), `currency`, `status`, `agency`, `tour_package`, `tourists` (nested writable), `hotel_bookings` (nested read-only), `flight_tickets` (nested read-only), `transfer_services` (nested read-only)

**`validate()` logic:**
- If user is AGENCY role: forces `agency = user.agency`, raises error if no agency assigned
- If user is NORMAL role: forces `agency = None`
- Admin/staff: no restrictions on agency

**`create()` logic:** creates the Reservation, then creates each Tourist from the `tourists[]` array.

**`update()` logic:**
- Updates reservation fields
- For each tourist in `tourists[]`: if `id` provided → updates existing tourist; if no `id` → creates new tourist

---

### 5.3 Views

#### `AdminReservationViewSet`
| Attribute | Value |
|-----------|-------|
| Base | `ModelViewSet` |
| Serializer | `ReservationSerializer` |
| Permission | `IsAdminUser` |
| Queryset | `Reservation.objects.all().order_by("-created_at")` |

#### `ClientReservationViewSet`
| Attribute | Value |
|-----------|-------|
| Base | `ModelViewSet` |
| Serializer | `ReservationSerializer` |
| Permission | `IsAuthenticated` |
| Queryset | `Reservation.objects.all().order_by("-created_at")` |

---

#### `AdminTouristViewSet` / `ClientTouristViewSet`
| Attribute | Value |
|-----------|-------|
| Base | `ModelViewSet` |
| Serializer | `TouristSerializer` |
| Permission | `IsAdminUser` / `IsAuthenticated` |

---

#### `AdminHotelBookingViewSet` / `ClientHotelBookingViewSet`
| Attribute | Value |
|-----------|-------|
| Base | `ModelViewSet` |
| Serializer | `HotelBookingSerializer` |
| Permission | `IsAdminUser` / `IsAuthenticated` |
| Queryset | `HotelBooking.objects.select_related("hotel_room__hotel", "selling_currency", "cost_currency")` |

**Custom `perform_create`:** after save, if status ≠ CANCELLED → `availability_count -= quantity`

**Custom `perform_destroy`:** if status ≠ CANCELLED → `availability_count += quantity` before delete

**Custom `perform_update`:** handles all combinations of status/quantity/room changes atomically

---

#### `AdminFlightTicketViewSet` / `ClientFlightTicketViewSet`
| Attribute | Value |
|-----------|-------|
| Base | `ModelViewSet` |
| Serializer | `FlightTicketSerializer` |
| Permission | `IsAdminUser` / `IsAuthenticated` |

---

#### `AdminExcursionBookingViewSet` / `ClientExcursionBookingViewSet`
| Attribute | Value |
|-----------|-------|
| Base | `ModelViewSet` |
| Serializer | `ExcursionBookingSerializer` |
| Permission | `IsAdminUser` / `IsAuthenticated` |

---

#### `AdminTransferServiceViewSet` / `ClientTransferServiceViewSet`
| Attribute | Value |
|-----------|-------|
| Base | `ModelViewSet` |
| Serializer | `TransferServiceSerializer` |
| Permission | `IsAdminUser` / `IsAuthenticated` |

---

#### `AdminExcursionServiceViewSet` / `ClientExcursionServiceViewSet`
| Attribute | Value |
|-----------|-------|
| Base | `ModelViewSet` |
| Serializer | `ExcursionServiceSerializer` |
| Permission | `IsAdminUser` / `IsAuthenticated` |

---

### 5.4 URLs / Endpoints

> Prefix: `/api/v1/reservations/`

#### Admin endpoints (`IsAdminUser`)

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `.../admin/reservations/` | List all reservations |
| `POST` | `.../admin/reservations/` | Create reservation |
| `GET` | `.../admin/reservations/{id}/` | Get reservation (includes nested tourists, hotel_bookings, flight_tickets, transfer_services) |
| `PUT` | `.../admin/reservations/{id}/` | Full update reservation + tourists |
| `PATCH` | `.../admin/reservations/{id}/` | Partial update reservation + tourists |
| `DELETE` | `.../admin/reservations/{id}/` | Delete reservation |
| `GET` | `.../admin/tourists/` | List all tourists |
| `POST` | `.../admin/tourists/` | Create tourist |
| `GET` | `.../admin/tourists/{id}/` | Get tourist |
| `PUT/PATCH` | `.../admin/tourists/{id}/` | Update tourist |
| `DELETE` | `.../admin/tourists/{id}/` | Delete tourist |
| `GET` | `.../admin/hotel-bookings/` | List hotel bookings |
| `POST` | `.../admin/hotel-bookings/` | Create hotel booking (deducts availability) |
| `GET` | `.../admin/hotel-bookings/{id}/` | Get hotel booking |
| `PUT/PATCH` | `.../admin/hotel-bookings/{id}/` | Update hotel booking (handles availability changes) |
| `DELETE` | `.../admin/hotel-bookings/{id}/` | Delete hotel booking (restores availability) |
| `GET` | `.../admin/flight-tickets/` | List flight tickets |
| `POST` | `.../admin/flight-tickets/` | Create flight ticket |
| `GET` | `.../admin/flight-tickets/{id}/` | Get flight ticket |
| `PUT/PATCH` | `.../admin/flight-tickets/{id}/` | Update flight ticket |
| `DELETE` | `.../admin/flight-tickets/{id}/` | Delete flight ticket |
| `GET` | `.../admin/excursion-bookings/` | List excursion bookings |
| `POST` | `.../admin/excursion-bookings/` | Create excursion booking |
| `GET` | `.../admin/excursion-bookings/{id}/` | Get excursion booking |
| `PUT/PATCH` | `.../admin/excursion-bookings/{id}/` | Update excursion booking |
| `DELETE` | `.../admin/excursion-bookings/{id}/` | Delete excursion booking |
| `GET` | `.../admin/transfer-services/` | List transfer services |
| `POST` | `.../admin/transfer-services/` | Create transfer service |
| `GET` | `.../admin/transfer-services/{id}/` | Get transfer service |
| `PUT/PATCH` | `.../admin/transfer-services/{id}/` | Update transfer service |
| `DELETE` | `.../admin/transfer-services/{id}/` | Delete transfer service |
| `GET` | `.../admin/excursion-services/` | List standalone excursion services |
| `POST` | `.../admin/excursion-services/` | Create excursion service |
| `GET` | `.../admin/excursion-services/{id}/` | Get excursion service |
| `PUT/PATCH` | `.../admin/excursion-services/{id}/` | Update excursion service |
| `DELETE` | `.../admin/excursion-services/{id}/` | Delete excursion service |

#### Client endpoints (`IsAuthenticated`)

Same set of endpoints under `.../client/...` — identical URL pattern, same serializers, same CRUD operations, but restricted to authenticated users only (not IsAdminUser).

| URL Prefix | Resources |
|------------|-----------|
| `.../client/reservations/` | Full CRUD |
| `.../client/tourists/` | Full CRUD |
| `.../client/hotel-bookings/` | Full CRUD |
| `.../client/flight-tickets/` | Full CRUD |
| `.../client/excursion-bookings/` | Full CRUD |
| `.../client/transfer-services/` | Full CRUD |
| `.../client/excursion-services/` | Full CRUD |

---

## 6. App: finance

### 6.1 Models

#### `Currency`

> File: `finance/models.py`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `code` | CharField(3) | unique | ISO 4217 e.g. `USD`, `TRY`, `EUR` |
| `name` | CharField(50) | | + `name_en`, `name_tr`, `name_ru` (modeltranslation) |
| `symbol` | CharField(5) | | e.g. `$`, `₺` |
| `is_active` | BooleanField | default True | Only active currencies returned to clients |

**Meta:** `ordering = ("code",)`

---

#### `ExchangeRate`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `base_currency` | FK → `Currency` | CASCADE | |
| `target_currency` | FK → `Currency` | CASCADE | |
| `rate` | DecimalField(10,4) | | How many target units = 1 base unit |
| `last_updated` | DateTimeField | auto_now | Auto-updated on every save |

**Unique constraint:** `(base_currency, target_currency)` — one rate per pair.

**Meta:** `ordering = ("-last_updated")`

---

#### `Invoice`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | | |
| `reservation` | OneToOneField → `reservations.Reservation` | CASCADE | One invoice per reservation |
| `net_amount` | DecimalField(12,2) | | Total cost/net |
| `sale_amount` | DecimalField(12,2) | | Total selling price |
| `profit` | DecimalField(12,2) | | `sale_amount - net_amount` |
| `agency_commission` | DecimalField(12,2) | | Commission owed to agency |
| `is_paid` | BooleanField | default False | |

**Meta:** `ordering = ("id",)`

---

### 6.2 Serializers

#### `CurrencySerializer`
Fields: `id`, `code`, `name`, `name_en`, `name_tr`, `name_ru`, `symbol`, `is_active`

#### `ExchangeRateSerializer`
Fields: `id`, `base_currency`, `target_currency`, `rate`, `last_updated` (read-only)

#### `InvoiceSerializer`
Fields: `id`, `reservation`, `net_amount`, `sale_amount`, `profit`, `agency_commission`, `is_paid`

---

### 6.3 Views

#### `AdminCurrencyViewSet`
| Base | `ModelViewSet` | Permission | `IsAdminUser` | Queryset: `Currency.objects.all().order_by("code")` |

#### `ClientCurrencyViewSet`
| Base | `ReadOnlyModelViewSet` | Permission | `AllowAny` | Queryset: `Currency.objects.filter(is_active=True)` |

#### `AdminExchangeRateViewSet`
| Base | `ModelViewSet` | Permission | `IsAdminUser` |

#### `ClientExchangeRateViewSet`
| Base | `ReadOnlyModelViewSet` | Permission | `AllowAny` |

#### `AdminInvoiceViewSet`
| Base | `ModelViewSet` | Permission | `IsAdminUser` |

#### `ClientInvoiceViewSet`
| Base | `ReadOnlyModelViewSet` | Permission | `IsAuthenticated` |

#### `ClientCurrencyConvertView`
| Base | `APIView` | Permission | `AllowAny` | Method | `GET` |

Query params: `from` (currency code), `to` (currency code), `amount`

Response:
```json
{
  "from": "USD",
  "to": "TRY",
  "amount": "100.00",
  "converted_amount": "3250.00",
  "effective_rate": "32.5000000000"
}
```

---

### 6.4 URLs / Endpoints

> Prefix: `/api/v1/finance/`

| Method | URL | Permission | Description |
|--------|-----|------------|-------------|
| `GET` | `.../admin/currencies/` | IsAdminUser | List all currencies |
| `POST` | `.../admin/currencies/` | IsAdminUser | Create currency |
| `GET` | `.../admin/currencies/{id}/` | IsAdminUser | Get currency |
| `PUT/PATCH` | `.../admin/currencies/{id}/` | IsAdminUser | Update currency |
| `DELETE` | `.../admin/currencies/{id}/` | IsAdminUser | Delete currency |
| `GET` | `.../admin/exchange-rates/` | IsAdminUser | List exchange rates |
| `POST` | `.../admin/exchange-rates/` | IsAdminUser | Create rate |
| `GET` | `.../admin/exchange-rates/{id}/` | IsAdminUser | Get rate |
| `PUT/PATCH` | `.../admin/exchange-rates/{id}/` | IsAdminUser | Update rate |
| `DELETE` | `.../admin/exchange-rates/{id}/` | IsAdminUser | Delete rate |
| `GET` | `.../admin/invoices/` | IsAdminUser | List invoices |
| `POST` | `.../admin/invoices/` | IsAdminUser | Create invoice |
| `GET` | `.../admin/invoices/{id}/` | IsAdminUser | Get invoice |
| `PUT/PATCH` | `.../admin/invoices/{id}/` | IsAdminUser | Update invoice |
| `DELETE` | `.../admin/invoices/{id}/` | IsAdminUser | Delete invoice |
| `GET` | `.../client/currencies/` | AllowAny | List active currencies |
| `GET` | `.../client/currencies/{id}/` | AllowAny | Get currency |
| `GET` | `.../client/exchange-rates/` | AllowAny | List exchange rates |
| `GET` | `.../client/exchange-rates/{id}/` | AllowAny | Get rate |
| `GET` | `.../client/invoices/` | IsAuthenticated | List invoices |
| `GET` | `.../client/invoices/{id}/` | IsAuthenticated | Get invoice |
| `GET` | `.../client/convert/?from=USD&to=TRY&amount=100` | AllowAny | Convert currency amount |

---

## 7. App: publicsite

### 7.1 Models

#### `HeroSection` — Singleton model

> File: `publicsite/models.py`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | always forced to `1` | Singleton — only one record exists |
| `badge_text` | CharField(120) | default set | Badge above headline |
| `logo` | ImageField | blank, null | Upload to `publicsite/logo/` |
| `image` | ImageField | blank, null | Upload to `publicsite/hero/` |
| `headline` | CharField(255) | default set | Main hero headline |
| `description` | TextField | default set | Hero description paragraph |
| `search_placeholder` | CharField(255) | default set | Search input placeholder |
| `search_button_text` | CharField(80) | default set | Search button label |
| `updated_at` | DateTimeField | auto_now | Last update timestamp |

**`save()` override:** always sets `pk = 1` before saving (enforces singleton pattern).

**`get_solo()` classmethod:** `get_or_create(pk=1)` — always returns the single instance.

---

### 7.2 Serializers

#### `HeroSectionSerializer`
Fields: `id`, `badge_text`, `logo`, `image`, `headline`, `description`, `search_placeholder`, `search_button_text`, `updated_at`
Read-only: `id`, `updated_at`

---

### 7.3 Views

#### `ClientHeroSectionView`
| Base | `generics.RetrieveAPIView` | Permission | `AllowAny` |
| `get_object()` | always returns `HeroSection.get_solo()` |
| Methods | `GET` only |

#### `AdminHeroSectionView`
| Base | `generics.RetrieveUpdateAPIView` | Permission | `IsAdminUser` |
| `get_object()` | always returns `HeroSection.get_solo()` |
| Parsers | `JSONParser`, `FormParser`, `MultiPartParser` (supports image uploads) |
| Methods | `GET`, `PUT`, `PATCH` |

---

### 7.4 URLs / Endpoints

> Prefix: `/api/v1/public-site/`

| Method | URL | Permission | Description |
|--------|-----|------------|-------------|
| `GET` | `/api/v1/public-site/client/hero/` | AllowAny | Get homepage hero section content |
| `GET` | `/api/v1/public-site/admin/hero/` | IsAdminUser | Get hero section (admin view) |
| `PUT` | `/api/v1/public-site/admin/hero/` | IsAdminUser | Full update hero section |
| `PATCH` | `/api/v1/public-site/admin/hero/` | IsAdminUser | Partial update hero section (supports image upload) |

---

## 8. Root URL Configuration

> File: `core/urls.py`

| URL | Handler | Description |
|-----|---------|-------------|
| `/admin/` | Django Admin | Django built-in admin panel |
| `/api/schema/` | `SpectacularAPIView` | OpenAPI schema (JSON) |
| `/api/schema/swagger-ui/` | `SpectacularSwaggerView` | Interactive Swagger docs |
| `/api/v1/accounts/` | `accounts.urls` | User management routes |
| `/api/v1/agencies/` | `agencies.urls` | Agency management routes |
| `/api/v1/inventory/` | `inventory.urls` | Inventory routes |
| `/api/v1/reservations/` | `reservations.urls` | Reservation routes |
| `/api/v1/finance/` | `finance.urls` | Finance routes |
| `/api/v1/public-site/` | `publicsite.urls` | Public site content routes |
| `/api/v1/auth/login/` | `TokenObtainPairView` | JWT login — returns `access` + `refresh` |
| `/api/v1/auth/refresh/` | `TokenRefreshView` | JWT token refresh |
| `/api/v1/auth/register/` | `RegisterView` | Normal user self-registration |
| `/media/<path>` | Static media serving | Uploaded images / files |

---

## 9. Permission Classes Summary

| Class | Location | Rule |
|-------|----------|------|
| `AllowAny` | DRF built-in | No authentication required |
| `IsAuthenticated` | DRF built-in | Any valid JWT token |
| `IsAdminUser` | DRF built-in | `is_staff=True` OR `is_superuser=True` |
| `IsAdminOrStaffRole` | `inventory/permissions.py` | `is_superuser` OR `is_staff` OR `role="STAFF"` — used for TourPackage admin endpoints |

---

## 10. Serializer Fields — Complete Reference

Quick lookup table: for each serializer, what fields are exposed and whether they are writable.

| Serializer | App | Write | Read-only | Notes |
|------------|-----|-------|-----------|-------|
| `RegisterSerializer` | accounts | email, first_name, last_name, phone_number, password, password2 | id | Public registration |
| `AdminCustomUserSerializer` | accounts | all | id | Full user control |
| `ClientCustomUserSerializer` | accounts | email, first_name, last_name, phone_number | id, role, agency, is_active | Self-service |
| `AdminAgencySerializer` | agencies | all fields | id | |
| `ClientAgencySerializer` | agencies | — | all (read-only view) | Excludes is_approved, approved_at |
| `AgencyRegisterSerializer` | agencies | name, agency_type, contact_person, email, phone, mobile_phone, skype_id, icq, account_email, account_first_name, account_last_name, account_phone_number, password, password2 | id, is_approved, approved_at | |
| `HotelFeatureSerializer` | inventory | name, name_en/tr/ru | id | |
| `HotelImageSerializer` | inventory | hotel, image, alt_text, order | id | |
| `HotelRoomSerializer` | inventory | all fields | id | Admin — shows cost_price |
| `ClientHotelRoomSerializer` | inventory | — | id, room fields, price (computed) | Hides agency_price, cost_price |
| `HotelSerializer` | inventory | hotel fields | id, features, gallery_images, rooms (nested) | Admin |
| `ClientHotelSerializer` | inventory | — | same but rooms use client serializer | |
| `FlightSerializer` | inventory | all fields | id | Admin |
| `ClientFlightSerializer` | inventory | — | all except agency_price, cost_price | price computed |
| `TourPackageSerializer` | inventory | all fields | id, minimum_cost_floor | Admin/staff |
| `ClientTourPackageSerializer` | inventory | — | id, name, destination, days, nights, currency, price | |
| `ExcursionSerializer` | inventory | all fields | id | Admin |
| `ClientExcursionSerializer` | inventory | — | all except agency_price, cost_price | price computed |
| `TransferProviderSerializer` | inventory | all fields | id | Admin |
| `TransferSerializer` | inventory | all fields | id | Admin |
| `ClientTransferSerializer` | inventory | — | all except agency_price, cost_price | price computed |
| `TouristSerializer` | reservations | all fields | — | id optional on write |
| `HotelBookingSerializer` | reservations | all fields | id | Includes availability validation |
| `FlightTicketSerializer` | reservations | all fields | id | |
| `ExcursionBookingSerializer` | reservations | all fields | id | |
| `TransferServiceSerializer` | reservations | all fields | id | |
| `ExcursionServiceSerializer` | reservations | all except system_date | id, system_date | Standalone |
| `ReservationSerializer` | reservations | all + tourists (inline) | id, created_at, hotel_bookings, flight_tickets, transfer_services | Nested create/update for tourists |
| `CurrencySerializer` | finance | all fields | id | |
| `ExchangeRateSerializer` | finance | base_currency, target_currency, rate | id, last_updated | |
| `InvoiceSerializer` | finance | all fields | id | |
| `HeroSectionSerializer` | publicsite | all except id, updated_at | id, updated_at | Singleton |

---

*End of document — covers all 6 apps, all models, all serializers, all views, and all endpoints.*
