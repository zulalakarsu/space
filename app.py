# import streamlit as st
# from PIL import Image
# import numpy as np
# import io
# import base64
# import torch
# import os
# import requests

# from groq import Groq
# from segment_anything import SamPredictor, sam_model_registry

# # Load Groq API key
# groq_key = os.environ.get("GROQ_API_KEY")
# client = Groq(api_key=groq_key)

# @st.cache_resource
# def load_sam_model():
#     sam = sam_model_registry["vit_b"](checkpoint="sam_checkpoints/sam_vit_b.pth")
#     predictor = SamPredictor(sam)
#     return predictor

# def segment_with_sam(predictor, image: Image.Image):
#     image_np = np.array(image.convert("RGB"))
#     predictor.set_image(image_np)
#     input_point = np.array([[image_np.shape[1] // 2, image_np.shape[0] // 2]])
#     input_label = np.array([1])
#     masks, _, _ = predictor.predict(point_coords=input_point, point_labels=input_label)
#     mask = masks[0]
#     image_np[~mask] = 0
#     return Image.fromarray(image_np)

# # def upload_image_to_fileio(image: Image.Image) -> str:
# #     buffered = io.BytesIO()
# #     image.save(buffered, format="PNG")
# #     buffered.seek(0)
# #     files = {'file': ('image.png', buffered, 'image/png')}
# #     response = requests.post("https://file.io", files=files)

# #     if response.status_code == 200 and response.json().get("success"):
# #         return response.json()["link"]
# #     else:
# #         raise Exception(f"File.io upload failed: {response.text}")

# def save_image_locally(image: Image.Image, filename: str = "test.png") -> str:
#     save_path = os.path.join("static", filename)
#     os.makedirs("static", exist_ok=True)
#     image.save(save_path, format="PNG")
#     # Return URL relative to the public app base path
#     return f"https://{os.environ.get('SPACE_ID')}.hf.space/static/{filename}"

# ## Added new line
# def call_groq_vision_api(prompt: str, image_url: str):
#     try:
#         completion = client.chat.completions.create(
#             model="meta-llama/llama-4-scout-17b-16e-instruct",
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "text", "text": prompt},
#                         {"type": "image_url", "image_url": {"url": image_url}}
#                     ]
#                 }
#             ],
#             temperature=0.7,
#             max_completion_tokens=1024,
#             top_p=1,
#             stream=False,
#             stop=None
#         )
#         return completion.choices[0].message.content
#     except Exception as e:
#         return f"[ERROR] Groq Vision API error: {str(e)}"

# # Streamlit UI
# st.set_page_config(page_title="Space Triage: Groq Vision")
# st.title("🚀 Space Triage - AI-Guided Ultrasound via Groq")

# target_organ = st.text_input("What do you wish to diagnose? (Target Organ)")
# uploaded_file = st.file_uploader("Upload an Ultrasound Image", type=["png", "jpg", "jpeg"])

# if target_organ and uploaded_file:
#     image = Image.open(uploaded_file)
#     st.image(image, caption="Uploaded Ultrasound Image", use_container_width=True)

#     with st.spinner("Uploading and analyzing organ..."):
#         try:
#             # image_url = upload_image_to_fileio(image)
#             image_url = save_image_locally(image, "uploaded.png")
#             # prompt = (
#             #     f"A user uploaded this ultrasound scan but wishes to diagnose the {target_organ}. "
#             #     f"First, identify which organ is in the scan. If it does NOT match the {target_organ}, "
#             #     f"give specific instructions on how to move the probe (e.g., left/right/down) to reach the {target_organ}."
#             # )
#             prompt = "Which organ is in the image? Give me just the name."
#             organ_feedback = call_groq_vision_api(prompt, image_url)
#         except Exception as e:
#             organ_feedback = f"[ERROR] Upload or analysis failed: {str(e)}"

#     st.subheader("🧭 Navigation Feedback / Organ Identification")
#     st.text(organ_feedback)

#     if "match" in organ_feedback.lower():
#         with st.spinner("Segmenting organ..."):
#             predictor = load_sam_model()
#             segmented_image = segment_with_sam(predictor, image)
#             st.image(segmented_image, caption="Segmented Organ", use_container_width=True)

#         with st.spinner("Uploading segmented image..."):
#             try:
#                 # segmented_url = upload_image_to_fileio(segmented_image)
#                 segmented_url = save_image_locally(segmented_image, "segmented.png")
#                 diagnosis_prompt = (
#                     f"This is a segmented ultrasound scan of the {target_organ}. "
#                     f"Diagnose the condition, mention any anomalies, and provide a short summary."
#                 )
#                 result = call_groq_vision_api(diagnosis_prompt, segmented_url)
#             except Exception as e:
#                 result = f"[ERROR] Upload or diagnosis failed: {str(e)}"

#         st.subheader("🔬 AI Diagnosis Output")
#         st.text(result)
#         st.success("Diagnosis complete.")
#     else:
#         st.warning("Organ mismatch. Please adjust the probe and re-upload the image.")


import streamlit as st
from PIL import Image

# Streamlit UI
st.set_page_config(page_title="Space Triage: Groq Vision")
st.title("🚀 Space Triage - AI-Guided Ultrasound (UI Preview Only)")

# Input: target organ
target_organ = st.text_input("What do you wish to diagnose? (Target Organ)")

# Input: upload image
uploaded_file = st.file_uploader("Upload an Ultrasound Image", type=["png", "jpg", "jpeg"])

if target_organ and uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="📷 Uploaded Ultrasound Image", use_container_width=True)

    st.subheader("🧭 Navigation Feedback / Organ Identification")
    st.info("🧪 Placeholder: This would show AI-generated organ identification and navigation advice.")

    # Simulate segmented image step
    st.subheader("🖼️ Segmented Organ (Simulated Output)")
    st.image(image, caption="🧪 Placeholder: Segmented organ image would appear here.", use_container_width=True)

    # Simulate diagnosis step
    st.subheader("🔬 AI Diagnosis Output")
    st.success("🧪 Placeholder: This would show AI-generated diagnosis based on the image.")
