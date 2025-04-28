import os
import io
import base64
from openai import OpenAI
from PIL import Image
# Initialize your OpenAI client
client = OpenAI(api_key="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")

# Read your reference image
reference_image_path = "/Users/bharadwajreddy/Downloads/22.png"  # The child's real photo you want to upload
img = Image.open(reference_image_path).convert("RGBA")

buf = io.BytesIO()
img.save(buf, format="PNG")
buf.name = "kid_reference.png"   # <— important so MIME = image/png
buf.seek(0)

# Your prompt
prompt = """
Create a detailed, high-quality children's storybook illustration:
In a dazzling space garden filled with colorful nebulae and twinkling stars, 
a little astronaut named Nikhil floats next to a large, friendly-looking elephant wearing a space helmet. 
They are peering into a transparent bubble containing a miniature Earth with swirling clouds and oceans. 
The elephant points its trunk at Africa, where a tiny giraffe is visible.

Make the astronaut child match the reference photo's face, curly hair, and happy expression.
Use rich colors, a child-friendly style, and warm lighting.
"""



# 4️⃣ Call the edit endpoint (uploads the child’s photo as reference)
# 4️⃣ Call the edit endpoint, passing in your PNG buffer
result = client.images.edit(
    model="gpt-image-1",
    image=[buf],            # 👈 use buf, not reference_image_bytes
    prompt=prompt,
    size="1024x1536",
    quality="high"
)

# 5️⃣ Decode & save the generated image
b64 = result.data[0].b64_json
img_bytes = base64.b64decode(b64)
with open("storybook_final.png", "wb") as out:
    out.write(img_bytes)

print("✅ Done! Saved as storybook_final.png")