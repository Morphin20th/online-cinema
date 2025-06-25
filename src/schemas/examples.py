BASE_AUTH_EXAMPLES = {
    "expired": "Token has expired.",
    "invalid": "Invalid token.",
    "header_format": "Invalid Authorization header format. Expected 'Bearer <token>'",
    "missing_header": "Authorization header is missing",
}

CURRENT_USER_EXAMPLES = {
    **BASE_AUTH_EXAMPLES,
    "blacklisted": "Token has been blacklisted.",
    "mismatch": "Token does not belong to the authenticated user.",
    "refresh_missing": "Refresh token not found.",
    "refresh_expired": "Refresh token expired.",
}

INVALID_CREDENTIAL_EXAMPLES = {
    **CURRENT_USER_EXAMPLES,
    "invalid_email_password": "Invalid email or password.",
}

ADMIN_REQUIRED_EXAMPLES = {
    "not_admin": "Access denied. Admin privileges required",
}

MODERATOR_OR_ADMIN_EXAMPLES = {
    "not_admin_moderator": "Access denied. Moderator or admin required",
}
