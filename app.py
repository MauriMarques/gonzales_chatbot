import random
import os
import requests
import image_classifier
from requests_toolbelt import MultipartEncoder
from flask import Flask, request, send_from_directory
from pymessenger.bot import Bot
from googletrans import Translator
from gtts import gTTS
from PIL import Image
import speech_recognition as sr
from pydub import AudioSegment
import telepot

app = Flask(__name__, static_folder="audio")

ACCESS_TOKEN = "EAAIj1rbKwNABALab50gBoXT2eMd1MYhFP0jw6MAG4eLVGwTKYufUxkZAAzllNGxo1Gu59xwloY8IEdJGvoaUOOXEkuJcLUbx4irhbZCvbyxEqss7m3vA5XkwhlxH8ZBQdvayq3IBw5vANx9mE6ec82BZBHHzH3z4qTaFJWQ75Yf0Lb9LX3sM"
VERIFY_TOKEN = "TOKENDOCHATBOT"
bot = Bot(ACCESS_TOKEN)
audio_path = "audio/audio.mp3"
received_audio_path = "audio/received_audio.aac"
received_audio_wav_path = "audio/received_audio.wav"
speech_recog = sr.Recognizer()

domain = "https://www.botgonzales.tk"

TOKEN = '635208413:AAEAXqp22Td5D74fvgFRzrwtN5r0FciZjzM'
TelegramBot = telepot.Bot(TOKEN)


@app.route('/audio/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    return send_from_directory('audio', filename)


@app.route('/' + TOKEN, methods=['POST'])
def receive_tel_message():
    try:
        message = request.get_json()
    except ValueError:
        return "Error"
    else:
        print(message)
        chat_id = message['message']['chat']['id']
        if message["message"].get("text"):
            response_sent_text = get_translated_message(message["message"].get("text"))
            generate_audio(response_sent_text)
            TelegramBot.sendMessage(chat_id, response_sent_text)
            TelegramBot.sendAudio(chat_id, domain + audio_path)
        elif message["message"].get("photo"):
            photo_id = message["message"].get("photo")
            TelegramBot.download_file(photo_id, "./photo.jpg")
            image = Image.open("photo.jpg")
            label = image_classifier.predict(image)
            translated_message = get_translated_message(label, src="en")
            generate_audio(translated_message)
            TelegramBot.sendMessage(chat_id, translated_message)
            TelegramBot.sendAudio(chat_id, domain + audio_path)

    return "Sucesso"


@app.route('/face', methods=['GET', 'POST'])
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

                        if attachments[0]["type"] == "image":
                            image = download_image_attachment(attachment_url)
                            label = image_classifier.predict(image)
                            translated_message = get_translated_message(label, src="en")
                            generate_audio(translated_message)
                            send_message(recipient_id, translated_message)
                        elif attachments[0]["type"] == "audio":
                            download_audio_attachment(attachment_url)
                            audio_message = get_audio_message()
                            translated_message = get_translated_message(audio_message)
                            generate_audio(translated_message)
                            send_message(recipient_id, translated_message)



    return "Message Processed"


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


def verify_fb_token(token_sent):
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Invalid verification token"


def get_translated_message(message_to_translate, src="pt"):
    translator = Translator()
    translation = translator.translate(message_to_translate, src=src, dest="es")
    return translation.text


def get_audio_message():
    audio_message = ""
    with sr.AudioFile(received_audio_wav_path) as source:
        audio = speech_recog.record(source)

    try:
        audio_message = speech_recog.recognize_google(audio, language="pt-BR")
        print("Sphinx thinks you said " + audio_message)
    except sr.UnknownValueError:
        print("Sphinx could not understand audio")
    except sr.RequestError as e:
        print("Sphinx error; {0}".format(e))

    return audio_message



def generate_audio(text):
    tts = gTTS(text, lang="es-es")
    tts.save(audio_path)


def get_message():
    sample_responses = ["You are stunning!", "We`re proud of you", "Keep on being you!", "We're greatful to know you :)"]
    return random.choice(sample_responses)


def download_image_attachment(url):
    return Image.open(requests.get(url, stream=True).raw)


def download_audio_attachment(url):
    doc = requests.get(url)
    open(received_audio_path, 'wb').write(doc.content)
    aac_version = AudioSegment.from_file(received_audio_path, "aac")
    aac_version.export(received_audio_wav_path, format="wav")


if __name__ == "__main__":
    app.run()