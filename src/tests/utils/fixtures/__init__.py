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
    genres_fixture,
    stars_fixture,
)
from src.tests.utils.fixtures.clients import (
    registered_user,
    registered_activated_user,
    token,
    regular_user,
    client_user,
    client_admin,
    client_moderator,
)
from src.tests.utils.fixtures.carts import (
    client_cart,
    client_cart_with_item,
)
from src.tests.utils.fixtures.orders import (
    order_fixture,
    order_paid_fixture,
)

__all__ = [
    # clients
    "registered_user",
    "registered_activated_user",
    "client_user",
    "client_moderator",
    "client_admin",
    "token",
    "regular_user",
    # movies
    "star_fixture",
    "director_fixture",
    "genre_fixture",
    "certification_fixture",
    "movie_fixture",
    "movies_fixture",
    "cart_fixture",
    "cart_item_fixture",
    "purchased_movie_fixture",
    "genres_fixture",
    "stars_fixture",
    # carts
    "client_cart",
    "client_cart_with_item",
    # orders
    "order_fixture",
    "order_paid_fixture",
]
