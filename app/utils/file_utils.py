import io
import fitz  # PyMuPDF
from PIL import Image

def load_image_from_bytes(file_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(file_bytes)).convert("RGB")

def pdf_to_images(pdf_bytes: bytes):
    images = []
    pdf = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page in pdf:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    return images