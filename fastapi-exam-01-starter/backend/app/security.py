
import os
import base64
import hashlib
import hmac
import json
import secrets

from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi.security import HTTPBearer


class JWTError(Exception):
    """Raised when a JWT is malformed or fails verification."""


_JWT_HASHES = {
    "HS256": hashlib.sha256,
    "HS384": hashlib.sha384,
    "HS512": hashlib.sha512,
}


def _jwt_b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _jwt_b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class _JWT:
    @staticmethod
    def encode(payload: dict, key: str, algorithm: str) -> str:
        digest = _JWT_HASHES.get(algorithm)
        if digest is None:
            raise ValueError(f"Unsupported JWT algorithm: {algorithm}")
        header = {"alg": algorithm, "typ": "JWT"}

        def serialize(value):
            if isinstance(value, datetime):
                return value.timestamp()
            raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

        signing_input = ".".join(
            (
                _jwt_b64encode(json.dumps(header, separators=(",", ":")).encode()),
                _jwt_b64encode(
                    json.dumps(payload, separators=(",", ":"), default=serialize).encode()
                ),
            )
        )
        signature = hmac.new(key.encode(), signing_input.encode("ascii"), digest).digest()
        return f"{signing_input}.{_jwt_b64encode(signature)}"

    @staticmethod
    def decode(token: str, key: str, algorithms: list[str]) -> dict:
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
            header = json.loads(_jwt_b64decode(encoded_header))
            payload = json.loads(_jwt_b64decode(encoded_payload))
            algorithm = header["alg"]
            digest = _JWT_HASHES.get(algorithm)
            if algorithm not in algorithms or digest is None:
                raise JWTError("Unsupported JWT algorithm")
            signing_input = f"{encoded_header}.{encoded_payload}"
            expected = hmac.new(key.encode(), signing_input.encode("ascii"), digest).digest()
            if not hmac.compare_digest(expected, _jwt_b64decode(encoded_signature)):
                raise JWTError("Invalid JWT signature")
            if "exp" in payload and float(payload["exp"]) <= datetime.now(timezone.utc).timestamp():
                raise JWTError("JWT has expired")
            if not isinstance(payload, dict):
                raise JWTError("Invalid JWT payload")
            return payload
        except JWTError:
            raise
        except (ValueError, TypeError, KeyError, IndexError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise JWTError("Invalid JWT") from exc


jwt = _JWT()


# ==================================
# ENVIRONMENT CONFIGURATION
# ==================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is missing from the .env file")

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)


# ==================================
# PASSWORD HASHING
# ==================================

_PBKDF2_ROUNDS = 600_000


def _ab64_encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii").replace("+", ".").rstrip("=")


def _ab64_decode(value: str) -> bytes:
    value = value.replace(".", "+")
    value += "=" * (-len(value) % 4)
    return base64.b64decode(value)


def get_password_hash(password: str):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS
    )
    return f"$pbkdf2-sha256${_PBKDF2_ROUNDS}${_ab64_encode(salt)}${_ab64_encode(digest)}"


def verify_password(plain_password: str, hashed_password: str):
    try:
        scheme, rounds, salt, expected = hashed_password.split("$")[1:]
        if scheme != "pbkdf2-sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), _ab64_decode(salt), int(rounds)
        )
        return hmac.compare_digest(digest, _ab64_decode(expected))
    except (ValueError, TypeError):
        return False


# ==================================
# JWT AUTHENTICATION
# ==================================

bearer_scheme = HTTPBearer()


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


# ==================================
# JWT TOKEN VERIFICATION
# ==================================

def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except (JWTError, TypeError, ValueError):
        return None
