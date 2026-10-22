"""Side-by-side review image: face test C vs bust_base at x3."""
from PIL import Image
from pipeline import pixgrid
a, _ = pixgrid.load("art/hand/S4/face_tests/C_dote.pix")
b, _ = pixgrid.load("art/hand/S4/bust/bust_base.pix")
A = pixgrid.to_image(a, 3, "#DFEAF6"); B = pixgrid.to_image(b, 3, "#DFEAF6")
W = Image.new("RGBA", (A.width + B.width + 18, max(A.height, B.height) + 12), (36, 22, 40, 255))
W.paste(A, (6, 6 + (B.height - A.height) // 2)); W.paste(B, (A.width + 12, 6))
W.save("00_REVIEW/r13_anime_pixel/bust/compare_C_vs_base_x3.png")
