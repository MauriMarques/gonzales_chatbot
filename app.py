import random
from flask import Flask, request
from pymessenger.bot import Bot
from googletrans import Translator


app = Flask(__name__)

ACCESS_TOKEN = "EAAIj1rbKwNABALab50gBoXT2eMd1MYhFP0jw6MAG4eLVGwTKYufUxkZAAzllNGxo1Gu59xwloY8IEdJGvoaUOOXEkuJcLUbx4irhbZCvbyxEqss7m3vA5XkwhlxH8ZBQdvayq3IBw5vANx9mE6ec82BZBHHzH3z4qTaFJWQ75Yf0Lb9LX3sM"
VERIFY_TOKEN = "TOKENDOCHATBOT"
bot = Bot(ACCESS_TOKEN)


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
                        send_message(recipient_id, response_sent_text)

                    if message["message"].get("attachments"):
                        response_sent_nontext = get_message()
                        send_message(recipient_id, response_sent_nontext)

    return "Message Processed"


def verify_fb_token(token_sent):
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Invalid verification token"


def get_translated_message(message_to_translate):
    translator = Translator()
    translation = translator.translate(message_to_translate, src="pt", dest="en")
    return translation.text


def get_message():
    sample_responses = ["You are stunning!", "We`re proud of you", "Keep on being you!", "We're greatful to know you :)"]
    return random.choice(sample_responses)


def send_message(recipient_id, response):
    bot.send_text_message(recipient_id, response)
    return "success"


if __name__ == "__main__":
    app.run()