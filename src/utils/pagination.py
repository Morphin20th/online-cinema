from fastapi import Request


def build_pagination_links(
    request: Request, page: int, per_page: int, total_pages: int
) -> tuple[str, str]:
    base_url = str(request.url).split("?")[0]

    next_page = (
        f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else ""
    )
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else ""
    return prev_page, next_page
