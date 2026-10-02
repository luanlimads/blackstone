from rembg import remove, new_session
from PIL import Image
import io
import sys

session = new_session("u2net")
input_path = sys.argv[1]
output_path = sys.argv[2]

with open(input_path, "rb") as f:
    input_data = f.read()

print("Removendo fundo...")
output_data = remove(input_data, session=session)

img = Image.open(io.BytesIO(output_data))
img.save(output_path, format="PNG")
print(f"Salvo em: {output_path}")
