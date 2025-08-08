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
    inactive_user,
    active_user,
    token,
    regular_user,
    client_admin,
    client_moderator,
    client_user,
    user_client_and_user,
    admin_client_and_user,
    moderator_client_and_user,
    active_user_and_payload,
    inactive_user_and_payload,
)
from src.tests.utils.fixtures.carts import (
    client_cart,
    client_cart_with_item,
)
from src.tests.utils.fixtures.orders import (
    order_fixture,
    order_paid_fixture,
)
from src.tests.utils.fixtures.payments import (
    stripe_service,
    client_stripe_mock,
    client_stripe_session_failure,
    stripe_session_failure_mock,
    stripe_service_mock,
    stripe_webhook_mock,
    client_webhook,
    payment_fixture,
)

__all__ = [
    # clients
    "inactive_user",
    "inactive_user_and_payload",
    "active_user",
    "admin_client_and_user",
    "moderator_client_and_user",
    "user_client_and_user",
    "client_moderator",
    "client_admin",
    "client_user",
    "token",
    "regular_user",
    "active_user_and_payload",
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
    # payments
    "stripe_service",
    "client_stripe_mock",
    "client_stripe_session_failure",
    "stripe_session_failure_mock",
    "stripe_service_mock",
    "stripe_webhook_mock",
    "client_webhook",
    "payment_fixture",
]
