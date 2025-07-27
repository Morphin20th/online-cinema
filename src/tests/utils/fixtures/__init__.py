from src.tests.utils.fixtures.movies import (
    certification_fixture,
    director_fixture,
    star_fixture,
    genre_fixture,
    movies_fixture,
    movie_fixture,
    cart_fixture,
    cart_item_fixture,
    purchased_movie_fixture,
)
from src.tests.utils.fixtures.clients import (
    registered_user,
    registered_and_activated_user,
    token,
    regular_user,
    client_authorized_by_user,
    client_authorized_by_admin,
    client_authorized_by_moderator,
)

__all__ = [
    "registered_user",
    "registered_and_activated_user",
    "client_authorized_by_user",
    "client_authorized_by_moderator",
    "client_authorized_by_admin",
    "token",
    "regular_user",
    "star_fixture",
    "director_fixture",
    "genre_fixture",
    "certification_fixture",
    "movie_fixture",
    "movies_fixture",
    "cart_fixture",
    "cart_item_fixture",
    "purchased_movie_fixture",
]
