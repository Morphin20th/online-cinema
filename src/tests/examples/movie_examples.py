minimal_movie_example = {
    "name": "inception",
    "year": 2010,
    "time": 148,
    "imdb": 8.8,
    "votes": 2_700_000,
    "description": "A thief who steals corporate secrets through the...",
    "price": 9.99,
    "certification": "pg-13",
    "genres": ["Sci-Fi", "Action"],
    "directors": ["Christopher Nolan"],
    "stars": ["Leonardo DiCaprio", "Joseph Gordon-Levitt"],
}

full_movie_example = {**minimal_movie_example, "meta_score": 87, "gross": 839_381_898}
invalid_movie_example = {
    "name": "",
    "year": 0,
    "time": -10,
    "imdb": 11.0,
    "genres": [],
    "directors": [],
    "stars": [],
}
