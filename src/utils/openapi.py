from src.schemas import ErrorResponseSchema


def aggregate_error_examples(
    description: str,
    examples: dict[str, str],
    model: type = ErrorResponseSchema,
) -> dict:
    return {
        "description": description,
        "model": model,
        "content": {
            "application/json": {
                "examples": {
                    name: {
                        "summary": name.replace("_", " ").capitalize(),
                        "value": {"detail": detail},
                    }
                    for name, detail in examples.items()
                }
            }
        },
    }
