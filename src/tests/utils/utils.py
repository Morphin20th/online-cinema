from io import BytesIO

from PIL import Image


def make_user_payload(email="test@user.com", password="Test1234!"):
    return {"email": email, "password": password}


def generate_test_image(file_format: str, size: tuple = (100, 100)) -> BytesIO:
    image = Image.new("RGB", size, color="red")
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format=file_format)
    img_byte_arr.seek(0)
    return img_byte_arr
