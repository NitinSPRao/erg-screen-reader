import os
import io
import openai
from google.cloud import vision
from google.cloud.vision_v1 import types
from PIL import Image
import pytesseract

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './igneous-aleph-394703-550f3acb3017.json'

client = vision.ImageAnnotatorClient()

image_path = "../ErgReader/erg.png"

with io.open(image_path, 'rb') as image_file:
    content = image_file.read()

image = types.Image(content=content)

# Use Google Cloud Vision to detect text in the image
response = client.text_detection(image=image)
texts = response.text_annotations

if texts:
    extracted_text = texts[0].description
    print('Detected text:')
    print(extracted_text)
else:
    print('No text detected')
    extracted_text = ""

if response.error.message:
    raise Exception(f'{response.error.message}')

api_key = os.getenv('OPENAI_API_KEY')

openai.api_key = api_key

# Make the request to the OpenAI API
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Please analyze the following intervals from the erg screen: {extracted_text}"}
    ]
)

print(response.choices[0].message['content'])
