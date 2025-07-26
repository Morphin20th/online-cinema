from tests.utils.utils import generate_test_image

profile_example = {
    "first_name": "james",
    "last_name": "bond",
    "gender": "man",
    "date_of_birth": "1990-01-01",
    "info": "Software developer with years of experience",
}

invalid_name_example = {
    "first_name": "test123",
    "last_name": "bond",
    "gender": "man",
}

invalid_gender_example = {
    "first_name": "james",
    "last_name": "bond",
    "gender": "invalid_gender",
}

future_birth_date_example = {
    "first_name": "james",
    "last_name": "bond",
    "date_of_birth": "2030-01-01",
}
past_birth_date_example = {
    "first_name": "james",
    "last_name": "bond",
    "date_of_birth": "1899-01-01",
}
invalid_large_image = {
    "avatar": ("large.jpg", b"x" * (int(1.5 * 1024 * 1024)), "image/jpeg")
}

invalid_file_format = {
    "avatar": ("test.bmp", generate_test_image("BMP").read(), "image/bmp")
}

invalid_byte = {"avatar": ("corrupt.jpg", b"not_an_image", "image/jpeg")}
