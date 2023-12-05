import json
import requests
import validators
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BITLY_ACCESS_TOKEN = os.getenv("BITLY_ACCESS_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")



def is_valid_url(url):
    # Use the validators package to check if the given string is a valid URL
    return validators.url(url)

def shorten_url(url):
    # Use Bitly API to shorten the given URL
    bitly_url = f'https://api-ssl.bitly.com/v4/shorten'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {BITLY_ACCESS_TOKEN}'
    }
    payload = {
        'long_url': url,
        'domain': 'bit.ly',
    }
    response = requests.post(bitly_url, headers=headers, json=payload)
    
    # Check for rate limit (HTTP status code 429)
    if response.status_code == 429:
        print("Bitly API rate limit exceeded. Please try again later.")
        # You can customize the rate limit message or take appropriate action here.
        return None
    
    return response.json().get('id')
    
def download_audio(file_id):
    # Get the file path from telegram
    request_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
    # Send the request
    r = requests.get(request_url)
    if r.status_code == 200:
        # Get the file path from the response
        file_path = r.json()['result']['file_path']
        # Download the file
        download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        r = requests.get(download_url)
        if r.status_code == 200:
            # Save the file
            prefix = "/tmp/" # Lambda only allows writing to /tmp
            file_path = prefix + file_path.split("/")[-1]
            with open(file_path, 'wb') as f:
                f.write(r.content)
            return file_path
        else:
            print("An error occurred while downloading the file")
            return None
        
def process_audio(file_path):
    # Send the file to OpenAI Whisper
    client = OpenAI(
        api_key=OPENAI_KEY,
    )
    audio_file = open(file_path, "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file,
        response_format="text"
    )
    return transcript


def lambda_handler(event, context):
    print(f"EVENT: {event}")
    print(f"CONTEXT: {context}")
    print(TELEGRAM_TOKEN)
    print(BITLY_ACCESS_TOKEN)
    print(OPENAI_KEY)

    # Parse the JSON string in event['body'] into a Python dictionary
    body = json.loads(event['body'])
    result = ""


    # Check if message has URL or audio
    # This is example request for a message with audio
    if 'voice' in body['message']:
        file_id = body['message']['voice']['file_id']
        print(f"File ID: {file_id}")
        file_path = download_audio(file_id)
        if file_path:
            transcript = process_audio(file_path)
            print(f"Transcript: {transcript}")
            result = transcript

        else:
            print("An error occurred while processing the audio")
            print(f"Code {r.status_code}")
            print(f"Response: {r.text}")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "An error occurred"})
            }

    # This is example request for a message with URL
    elif 'text' in body['message']:
        message = body['message']['text']
        print(f"Message: {message}")
        if is_valid_url(message):
            short_url = shorten_url(message)
            print(f"The short URL is: {short_url}")
            result = short_url
        else:
            print("Not a valid URL. Abandoning ship.")
            return {
                "statusCode": 200,
            }

    else:
        print("Not a valid message. Abandoning ship.")
        return {
            "statusCode": 200,
        }
    
    # Send the response back to Telegram
    response_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': body['message']['chat']['id'],
        'text': result
    }
    r = requests.post(response_url, json=payload)
    print(f"Response: {r.status_code}")
    return {
        "statusCode": 200,
    }
