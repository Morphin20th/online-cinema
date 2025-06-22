from typing import Tuple, Optional

from fastapi import Request, Query


class Paginator:
    def __init__(
        self,
        request: Request,
        query: Query,
        page: int = 1,
        per_page: int = 10,
        base_params: Optional[dict] = None,
    ) -> None:
        self.request = request
        self.query = query
        self.page = page
        self.per_page = per_page
        self.base_params = base_params or {}
        self.total_items = 0
        self.total_pages = 0

    @staticmethod
    def _paginate_query(
        query: Query,
        page: int,
        per_page: int,
    ) -> Tuple[Query, int, int]:
        total_items = query.count()
        total_pages = (total_items + per_page - 1) // per_page
        offset = (page - 1) * per_page

        paginated_query = query.offset(offset).limit(per_page)
        return paginated_query, total_pages, total_items

    def paginate(self) -> Query:
        self.query, self.total_pages, self.total_items = self._paginate_query(
            self.query, self.page, self.per_page
        )
        return self.query

    def get_links(self) -> Tuple[Optional[str], Optional[str]]:
        params = self.base_params.copy()
        params.update({"page": self.page, "per_page": self.per_page})

        prev_page = None
        next_page = None

        if self.page > 1:
            prev_params = params.copy()
            prev_params["page"] = self.page - 1
            prev_page = str(self.request.url.replace_query_params(**prev_params))

        if self.page < self.total_pages:
            next_params = params.copy()
            next_params["page"] = self.page + 1
            next_page = str(self.request.url.replace_query_params(**next_params))

        return prev_page, next_page
