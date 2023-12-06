import json
import requests
import validators
from openai import OpenAI
from dotenv import load_dotenv
import os

def is_valid_url(url):
    # Use the validators package to check if the given string is a valid URL
    return validators.url(url)

def shorten_url(url):
    # Use Bitly API to shorten the given URL
    bitly_url = f'https://api-ssl.bitly.com/v4/shorten'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("BITLY_ACCESS_TOKEN")}'
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
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    # Get the file path from telegram
    request_url = f"https://api.telegram.org/bot{telegram_token}/getFile?file_id={file_id}"
    # Send the request
    r = requests.get(request_url)
    if r.status_code == 200:
        # Get the file path from the response
        file_path = r.json()['result']['file_path']
        # Download the file

        download_url = f"https://api.telegram.org/file/bot{telegram_token}/{file_path}"
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
    else:
        print("An error occurred while getting the file path")
        print(f"Response status: {r.status_code}")
        print(f"Response body: {r.json()}")
        return None
        
def process_audio(file_path):
    # Send the file to OpenAI Whisper
    client = OpenAI(
        api_key=os.getenv("OPENAI_KEY"),
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
    #print(f"CONTEXT: {context}")
    load_dotenv()  # take environment variables from .env

    # Parse the JSON string in event['body'] into a Python dictionary
    body = json.loads(event['body'])
    result = ""


    # Check if message has URL or audio
    # This is example request for a message with audio
    # Check if 'message' is in body
    if 'message' in body:
        # Check if 'voice' is in 'message'
        if 'voice' in body['message']:
            file_id = body['message']['voice']['file_id']
            file_path = download_audio(file_id)
            if file_path:
                transcript = process_audio(file_path)
                result = transcript
            else:
                print("An error occurred while processing the audio")
                return {
                    "statusCode": 500,
                    "body": json.dumps({"message": "An error occurred"})
                }
        # Check if 'text' is in 'message'
        elif 'text' in body['message']:
            message = body['message']['text']
            if is_valid_url(message):
                short_url = shorten_url(message)
                result = short_url
            else:
                print("Not a valid URL. Abandoning ship.")
                return {
                    "statusCode": 200,
                }
        else:
            print("Not a valid message. Abandoning ship.")
            print("This is the full telegram request: ")
            print(body)
            return {
                "statusCode": 200,
            }
    else:
        print("'message' key not found in the body.")
        print("This is the full telegram request: ")
        print(body)
        return {
            "statusCode": 200,
        }
    
    # Send the response back to Telegram
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    response_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        'chat_id': body['message']['chat']['id'],
        'text': result,
        'reply_to_message_id': body['message']['message_id']  # Add this line to include the reply_to_message_id
    }
    r = requests.post(response_url, json=payload)
    print(f"Response: {r.status_code}")
    return {
        "statusCode": 200,
    }

