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
    "refresh_expired": "Refresh token expired.",
}

INVALID_CREDENTIAL_EXAMPLES = {
    **CURRENT_USER_EXAMPLES,
    "invalid_email_password": "Invalid email or password.",
}

ADMIN_REQUIRED_EXAMPLES = {
    "not_admin": "Access denied. Admin privileges required.",
}

MODERATOR_OR_ADMIN_EXAMPLES = {
    "not_admin_moderator": "Access denied. Moderator or admin required.",
}

PROFILE_VALIDATION_EXAMPLES = {
    "empty_info": "Info cannot be empty or whitespace only.",
    "invalid_first_name": "test23 contains non-english letters",
    "invalid_last_name": "test23 contains non-english letters",
    "invalid_birth_date": "You must be at least 18 years old to register.",
    "birth_date_year_too_old": "Invalid birth date - year must be greater than 1900.",
    "invalid_gender": "Gender must be one of: man, woman, other",
    "invalid_image_format": "Unsupported image format: BMP. Use one of next: ['JPG', 'JPEG', 'PNG']",
    "invalid_image_size": "Image size exceeds 1 MB",
    "corrupted_image": "Invalid image format",
}


STRIPE_ERRORS_EXAMPLES = {
    "invalid_signature": "Invalid Stripe webhook signature.",
    "invalid_payload": "Invalid Stripe webhook payload.",
    "refund_failed": "Stripe refund error:",
    "order_no_items": "Order has no items.",
}
