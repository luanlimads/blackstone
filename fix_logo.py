from PIL import Image
import sys

input_path = sys.argv[1]
output_path = sys.argv[2]

img = Image.open(input_path).convert('RGBA')
w,h = img.size
pixels = img.load()
for x in range(w):
  for y in range(h):
    r,g,b,a = pixels[x,y]
    if a > 50:
      # If it's mostly dark (not red, not white)
      if r < 100 and g < 100 and b < 100:
        pixels[x,y] = (255, 255, 255, a)
img.save(output_path)
print(f"Salvo em: {output_path}")
