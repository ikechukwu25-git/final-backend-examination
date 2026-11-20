# Okwu Couriers API: Contract (TEKHUB FastAPI Practical 01)

Your API must start with `uvicorn app.main:app --port 8000`. It is marked by an automated script that calls the endpoints below, so use these paths, field names, status values and status codes exactly.

## Endpoints

| Method | Path | Token | Success and errors |
|---|---|---|---|
| GET | /health | No | 200 `{"status": "ok"}` |
| POST | /auth/register | No | 201 user `{id, name, email}`. 409 duplicate email. 422 invalid input |
| POST | /auth/login | No | 200 `{"access_token": "...", "token_type": "bearer"}`. 401 wrong email or password |
| GET | /auth/me | Yes | 200 the logged-in user |
| POST | /parcels | Yes | 201 the new parcel. 422 invalid input |
| GET | /parcels | Yes | 200 `{items, total, page, size}`, own parcels only, newest first |
| GET | /parcels/{id} | Yes | 200 parcel. 404 missing or not yours |
| PATCH | /parcels/{id}/status | Yes | 200 updated parcel. 409 not allowed. 422 unknown status |
| DELETE | /parcels/{id} | Yes | 204. 409 if status is not CREATED. 404 missing or not yours |
| GET | /track/{tracking_code} | No | 200 public view. 404 unknown code |

Protected routes use `Authorization: Bearer <token>`. Missing, fake or expired token: 401.

## Users

- `name`: 2 to 80 characters. `email`: valid, unique, case-insensitive. `password`: at least 8 characters.
- Store only a bcrypt or argon2 hash. Never return the password or its hash.

## Parcel fields

Request: `sender_name`, `recipient_name` (2 to 80 chars), `recipient_phone`, `origin_city`, `destination_city`, `weight_kg`.

Response adds: `id`, `tracking_code`, `price`, `status`, `created_at`.

- `recipient_phone`: `08031234567` style (11 digits, starts 070/080/081/090/091) or `+2348031234567`.
- Cities: Awka, Onitsha, Nnewi, Enugu, Asaba, Owerri. Any letter case accepted; stored and returned in title case.
- `weight_kg`: greater than 0, at most 50.
- `tracking_code`: `OKW-` + 8 random uppercase letters or digits, unique.
- `price` (naira, whole number) = 1500 + 400 x ceil(weight_kg) + 1000 if origin and destination differ.
  - 2.3 kg Awka to Enugu = 3700. 1 kg Awka to Awka = 1900.
- List query: `status` (optional), `page` (default 1, min 1), `size` (default 10, max 50; 51 or more gives 422).
- Someone else's parcel returns 404 (not 403).

## Status workflow

PATCH body: `{"status": "PICKED_UP", "note": "optional, max 200 chars"}`

| Current | Allowed next |
|---|---|
| CREATED | PICKED_UP, CANCELLED |
| PICKED_UP | IN_TRANSIT |
| IN_TRANSIT | OUT_FOR_DELIVERY |
| OUT_FOR_DELIVERY | DELIVERED, FAILED_DELIVERY |
| FAILED_DELIVERY | OUT_FOR_DELIVERY, RETURNED |
| DELIVERED, RETURNED, CANCELLED | none (final) |

Anything else: 409. Every change (including the initial CREATED) is saved to history with note and timestamp.

## Public tracking response

```json
{
  "tracking_code": "OKW-7K2QX9AB",
  "status": "IN_TRANSIT",
  "origin_city": "Awka",
  "destination_city": "Enugu",
  "history": [
    {"status": "CREATED", "note": "Parcel created", "timestamp": "2026-11-20T10:00:00Z"},
    {"status": "PICKED_UP", "note": "Picked up at Awka office", "timestamp": "2026-11-20T10:30:00Z"},
    {"status": "IN_TRANSIT", "note": null, "timestamp": "2026-11-20T11:00:00Z"}
  ]
}
```

History is oldest first. Never include names, phone number or owner details.
