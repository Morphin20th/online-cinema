from fastapi import Request
from starlette.datastructures import URL

from src.database import MovieModel
from src.utils import Paginator


def make_fake_request(
    base_url: str = "http://testserver/movies",
    params: dict = None,
):
    scope = {
        "type": "http",
        "method": "GET",
        "headers": [],
        "query_string": b"",
        "path": "/movies",
        "server": ("testserver", 80),
    }
    request = Request(scope)
    if params:
        request._url = URL(base_url).include_query_params(**params)
    return request


def test_paginator_paginate_basic(db_session, movies_fixture):
    movies_fixture(25)
    query = db_session.query(MovieModel)
    request = make_fake_request(params={"page": 1, "per_page": 10})

    paginator = Paginator(request=request, query=query, page=1, per_page=10)
    result = paginator.paginate().all()

    assert len(result) == 10
    assert paginator.total_items == 25
    assert paginator.total_pages == 3


def test_paginator_last_page(db_session, movies_fixture):
    movies_fixture(25)
    query = db_session.query(MovieModel)
    request = make_fake_request(params={"page": 3, "per_page": 10})

    paginator = Paginator(request=request, query=query, page=3, per_page=10)
    result = paginator.paginate().all()

    assert len(result) == 5
    assert paginator.total_items == 25
    assert paginator.total_pages == 3


def test_paginator_prev_next_links(db_session, movies_fixture):
    movies_fixture(25)
    query = db_session.query(MovieModel)
    request = make_fake_request(params={"page": 2, "per_page": 10})

    paginator = Paginator(request=request, query=query, page=2, per_page=10)
    paginator.paginate()
    prev_link, next_link = paginator.get_links()

    assert "page=1" in prev_link
    assert "page=3" in next_link


def test_paginator_first_page_links(db_session, movies_fixture):
    movies_fixture(25)
    query = db_session.query(MovieModel)
    request = make_fake_request(params={"page": 1, "per_page": 10})

    paginator = Paginator(request=request, query=query, page=1, per_page=10)
    paginator.paginate()
    prev_link, next_link = paginator.get_links()

    assert prev_link is None
    assert "page=2" in next_link


def test_paginator_single_page(db_session, movies_fixture):
    movies_fixture(25)
    query = db_session.query(MovieModel).limit(5)
    request = make_fake_request(params={"page": 1, "per_page": 10})

    paginator = Paginator(request=request, query=query, page=1, per_page=10)
    paginator.paginate()
    prev_link, next_link = paginator.get_links()

    assert paginator.total_pages == 1
    assert next_link is None
    assert prev_link is None
