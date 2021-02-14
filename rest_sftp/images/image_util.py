import io

from PIL import Image


def get_thumbnail_as_bytes(width, height, filepath):
    im = Image.open(filepath)
    im.thumbnail((width, height), Image.ANTIALIAS)
    content = io.BytesIO()
    im.save(content, "jpeg")
    content.seek(0)
    return content
