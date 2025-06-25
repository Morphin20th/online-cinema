from fastapi import status

from src.schemas.common import ErrorResponseSchema


def generate_error_response(status_code: int, description: str, example: str) -> dict:
    return {
        status_code: {
            "description": description,
            "model": ErrorResponseSchema,
            "content": {"application/json": {"example": {"detail": example}}},
        }
    }


def base_auth_examples() -> dict:
    return {
        "expired": {
            "summary": "Expired",
            "value": {"detail": "Token has expired."},
        },
        "invalid": {
            "summary": "Invalid",
            "value": {"detail": "Invalid token."},
        },
        "header_format": {
            "summary": "Wrong Authentication Header Format",
            "value": {
                "detail": "Invalid Authorization header format. Expected 'Bearer <token>'"
            },
        },
        "missing_header": {
            "summary": "Authentication header is missing",
            "value": {"detail": "Authorization header is missing"},
        },
    }


def base_token_401_response() -> dict:
    return {
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized: Token is expired or invalid.",
            "content": {
                "application/json": {
                    "examples": base_auth_examples(),
                }
            },
            "model": ErrorResponseSchema,
        }
    }


def current_user_responses() -> dict:
    examples = {
        **base_auth_examples(),
        "blacklisted": {
            "summary": "Blacklisted",
            "value": {"detail": "Token has been blacklisted."},
        },
        "mismatch": {
            "summary": "Mismatch",
            "value": {"detail": "Token does not belong to the authenticated user."},
        },
        "refresh_missing": {
            "summary": "Refresh token not found",
            "value": {"detail": "Refresh token not found."},
        },
        "refresh_expired": {
            "summary": "Refresh token expired",
            "value": {"detail": "Refresh token expired."},
        },
    }

    return {
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Unauthorized: Token is invalid, expired, blacklisted, or mismatched.\n\n"
                "Possible reasons:\n"
                "- Token has expired.\n"
                "- Invalid token.\n"
                "- Token is blacklisted.\n"
                "- Token does not belong to current user.\n"
                "- Refresh token not found or expired.\n"
                "- Malformed or missing Authorization header."
            ),
            "content": {"application/json": {"examples": examples}},
            "model": ErrorResponseSchema,
        },
        **generate_error_response(
            status.HTTP_403_FORBIDDEN,
            "Forbidden: Inactive user.",
            "Inactive user.",
        ),
    }


def unauthorized_401_with_invalid_email_password() -> dict:
    base = current_user_responses()

    extended_examples = {
        **base[status.HTTP_401_UNAUTHORIZED]["content"]["application/json"]["examples"],
        "invalid_email_password": {
            "summary": "Invalid email or password.",
            "value": {"detail": "Invalid email or password."},
        },
    }

    return {
        status.HTTP_401_UNAUTHORIZED: {
            **base[status.HTTP_401_UNAUTHORIZED],
            "content": {"application/json": {"examples": extended_examples}},
        },
        status.HTTP_403_FORBIDDEN: base[status.HTTP_403_FORBIDDEN],
    }
