def password_validation(value: str) -> str:
    if (
        not any(c.islower() for c in value)
        or not any(c.isupper() for c in value)
        or not any(c.isdigit() for c in value)
        or not any(c in "@$!%*?&" for c in value)
    ):
        raise ValueError(
            "Password must contain 8-32 characters, "
            "at least one uppercase and lowercase letter, "
            "a number and a special character"
        )
    return value
