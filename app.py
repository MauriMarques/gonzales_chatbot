import random
import os
import requests
import numpy as np
import urllib.request
import image_classifier
from requests_toolbelt import MultipartEncoder
from flask import Flask, request
from pymessenger.bot import Bot
from googletrans import Translator
from gtts import gTTS
from PIL import Image


app = Flask(__name__)

ACCESS_TOKEN = "EAAIj1rbKwNABALab50gBoXT2eMd1MYhFP0jw6MAG4eLVGwTKYufUxkZAAzllNGxo1Gu59xwloY8IEdJGvoaUOOXEkuJcLUbx4irhbZCvbyxEqss7m3vA5XkwhlxH8ZBQdvayq3IBw5vANx9mE6ec82BZBHHzH3z4qTaFJWQ75Yf0Lb9LX3sM"
VERIFY_TOKEN = "TOKENDOCHATBOT"
bot = Bot(ACCESS_TOKEN)
audio_path = "audio.mp3"

@app.route('/', methods=['GET', 'POST'])


def receive_message():
    if request.method == 'GET':
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    else:
        output = request.get_json()
        for event in output["entry"]:
            messaging = event["messaging"]
            for message in messaging:
                if message.get("message"):
                    recipient_id = message["sender"]["id"]
                    if message["message"].get("text"):
                        response_sent_text = get_translated_message(message["message"].get("text"))
                        generate_audio(response_sent_text)
                        send_message(recipient_id, response_sent_text)

                    if message["message"].get("attachments"):
                        attachments = message["message"].get("attachments")
                        attachment_url = attachments[0]["payload"]["url"]
                        image = download_image_attachment(attachment_url)
                        label = image_classifier.predict(image)
                        generate_audio(label)
                        send_message(recipient_id, label)


    return "Message Processed"


def verify_fb_token(token_sent):
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Invalid verification token"


def get_translated_message(message_to_translate):
    translator = Translator()
    translation = translator.translate(message_to_translate, src="pt", dest="en")
    return translation.text


def generate_audio(text):
    tts = gTTS(text)
    tts.save(audio_path)


def get_message():
    sample_responses = ["You are stunning!", "We`re proud of you", "Keep on being you!", "We're greatful to know you :)"]
    return random.choice(sample_responses)


def send_message(recipient_id, response):
    bot.send_text_message(recipient_id, response)
    send_audio(recipient_id)
    return "success"


def send_audio(recipient_id):
    payload = dict()
    payload['recipient'] = str({
        'id': recipient_id
    })
    payload['notification_type'] = "REGULAR"
    payload['message'] = str({
        'attachment': {
            'type': "audio",
            'payload': {}
        }
    })
    payload['filedata'] = (os.path.basename(audio_path), open(audio_path, 'rb'), "audio/mp3")

    multipart_data = MultipartEncoder(payload)
    multipart_header = {
        'Content-Type': multipart_data.content_type
    }
    return requests.post('{0}/me/messages'.format(bot.graph_url), data=multipart_data,
                         params=bot.auth_args, headers=multipart_header).json()


def download_image_attachment(url):
    return Image.open(requests.get(url, stream=True).raw)


if __name__ == "__main__":
    app.run()