import base64
import os
import re
from openai import OpenAI

images_dir = 'street_images'
captions_dir = 'street_captions'
street_images = {}
addresses = []
def repopulate_street_images():
    global street_images, addresses
    street_images.clear()
    addresses.clear()
    for address in os.listdir(images_dir):
        street_address = address.split('_')[0]
        if address.endswith('.jpg'):
            if street_address not in addresses:
                addresses.append(street_address)
            if street_address not in street_images:
                street_images[street_address] = []
            street_images[street_address].append(f'./street_images/{address}')

def _inference(images: list, text_prompt: str) -> str:
    client = OpenAI(api_key="123", base_url="http://ailadgx-gpu40.utsarr.net:2530/v1")

    # Build content with text and images
    content = [{"type": "text", "text": text_prompt}]
    for image_base64 in images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
        })

    response = client.chat.completions.create(
        model="Qwen/Qwen3-VL-8B-Instruct-FP8",
        messages=[{"role": "user", "content": content}]
    )
    result = response.choices[0].message.content
    clean_content = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()
    return clean_content

def _getStreetImages(address: str) -> list:
    estate_images = []
    if address in street_images and len(street_images[address]) > 0:
        for image_path in street_images[address]:
            with open(image_path, 'rb') as img_file:
                estate_images.append(base64.b64encode(img_file.read()).decode('utf-8'))
    return estate_images

import json
def _saveCaption(address: str, caption: dict) -> None:
    with open(captions_dir + '/' + address + '.json', 'w+') as file:
        json.dump(caption, file)

def getCaption(address: str) -> dict:
    for file in os.listdir(captions_dir):
        if file.endswith(".json"):
            file_address = file.replace(".json", "")
            if file_address == address:
                with open(captions_dir + '/' + address + '.json', 'r') as f:
                    return json.load(f)
    return {}

def inferenceAddress(address: str, text_prompt: str) -> str:
    global street_images
    print(f'Processing address: {address} with text prompt: {text_prompt}')
    return _inference(_getStreetImages(address), text_prompt)

def processAddress(address: str) -> None:
    global captions_dir, images_dir, street_images
    caption = {"estateType": inferenceAddress(address, "Is this residential or commercial? Simply say residential or simply say commercial.")}
    if caption["estateType"] == "residential":
        caption["Is the lawn well kept?"] = inferenceAddress(address, "Is the lawn for this residential address well kept? Simply say Yes, No or N/A.")
        caption["Is there evidence of commercial activity?"] = inferenceAddress(address, "Is there evidence of commercial activity at this residential address? Simply say Yes, No or N/A.")
        caption["Is there structural damage?"] = inferenceAddress(address, "Is there structural damage of the house? Simply say Yes, No or N/A.")
        caption["Rate the lawn by quality (1-10)"] = inferenceAddress(address, "Rate the lawn by quality adherence (1-10). Simply say a number between 1 to 10 with 1 being worst and 10 being best or N/A if there is not lawn.")
        caption["Is this property mixed-use?"] = inferenceAddress(address, "Is this property mixed-use (commercial + residential)? Simply answer Yes or No.")
    elif caption["estateType"] == "commercial":
        caption["Is the building in good condition?"] = inferenceAddress(address, "Is the building in good condition? Simply say Yes, No or N/A.")
        caption["Activity type by appearence"] = inferenceAddress(address, "Commercial appearence, what type of activity does it look like the estate suggests it does? Name the primary activity in 1-3 words as to what the activity is or say shutdown if it looks inactive.")
        caption["Does this location look active?"] = inferenceAddress(address, "Commercial appearence, does this estate look commericially active? Simply say Yes or No")
        caption["Rate the level of activity (1-10)?"] = inferenceAddress(address, "Commercial appearence, rate the level of activity that appears here (1-10)? Simply say a number between 1 tp 10 with 1 being no activity and 10 being most activity")
        caption["Rate the estate quality (1-10)?"] = inferenceAddress(address, "rate the building or estate quality for commercial work. (1-10)? If instead of rating parking lots as low potential, instead rate them above average potential in your consideration but come up with your own rating. Simply say a number from 1 to 10 1 being no activity and 10 being most activity")
        caption["Is this property mixed-use?"] = inferenceAddress(address, "Is this property mixed-use (commercial + residential)? Simply answer Yes or No.")
    _saveCaption(address, caption)




if __name__ == "__main__":
    for street_address in addresses:
        processAddress(street_address)