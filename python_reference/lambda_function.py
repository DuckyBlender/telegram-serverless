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
    # {'version': '2.0', 'routeKey': 'POST /duckShortenerTelegram', 'rawPath': '/duckShortenerTelegram', 'rawQueryString': '', 'headers': {'accept-encoding': 'gzip, deflate', 'content-length': '633', 'content-type': 'application/json', 'host': 'qb76wpzrm8.execute-api.eu-central-1.amazonaws.com', 'x-amzn-trace-id': 'Root=1-656f9d06-45b6d8ba54ac568411629b53', 'x-forwarded-for': '91.108.6.95', 'x-forwarded-port': '443', 'x-forwarded-proto': 'https'}, 'requestContext': {'accountId': '534406734576', 'apiId': 'qb76wpzrm8', 'domainName': 'qb76wpzrm8.execute-api.eu-central-1.amazonaws.com', 'domainPrefix': 'qb76wpzrm8', 'http': {'method': 'POST', 'path': '/duckShortenerTelegram', 'protocol': 'HTTP/1.1', 'sourceIp': '91.108.6.95', 'userAgent': ''}, 'requestId': 'PfV5EhsJFiAEJqg=', 'routeKey': 'POST /duckShortenerTelegram', 'stage': '$default', 'time': '05/Dec/2023:21:58:30 +0000', 'timeEpoch': 1701813510505}, 'body': '{"update_id":147759372,\n"message":{"message_id":50,"from":{"id":5337682436,"is_bot":false,"first_name":"DuckyBlender","username":"DuckyBlender","language_code":"en"},"chat":{"id":5337682436,"first_name":"DuckyBlender","username":"DuckyBlender","type":"private"},"date":1701813510,"forward_from":{"id":6442355191,"is_bot":false,"first_name":"Mloda","last_name":"Alchimiczka","username":"Alchimiczka","language_code":"en"},"forward_date":1701799632,"voice":{"duration":24,"mime_type":"audio/ogg","file_id":"AwACAgQAAxkBAAMyZW-dBiH0AAHwICKISxifj-dcnDGOAAJwEQACl_aBUzgXY_cj1hcaMwQ","file_unique_id":"AgADcBEAApf2gVM","file_size":94966}}}', 'isBase64Encoded': False}

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

    # This is example request for a message with URL
    # {'version': '2.0', 'routeKey': 'POST /duckShortenerTelegram', 'rawPath': '/duckShortenerTelegram', 'rawQueryString': '', 'headers': {'accept-encoding': 'gzip, deflate', 'content-length': '398', 'content-type': 'application/json', 'host': 'qb76wpzrm8.execute-api.eu-central-1.amazonaws.com', 'x-amzn-trace-id': 'Root=1-656a6d86-4553121c13ba59c308e77f47', 'x-forwarded-for': '91.108.6.95', 'x-forwarded-port': '443', 'x-forwarded-proto': 'https'}, 'requestContext': {'accountId': '534406734576', 'apiId': 'qb76wpzrm8', 'domainName': 'qb76wpzrm8.execute-api.eu-central-1.amazonaws.com', 'domainPrefix': 'qb76wpzrm8', 'http': {'method': 'POST', 'path': '/duckShortenerTelegram', 'protocol': 'HTTP/1.1', 'sourceIp': '91.108.6.95', 'userAgent': ''}, 'requestId': 'PSYM_i61FiAEPoA=', 'routeKey': 'POST /duckShortenerTelegram', 'stage': '$default', 'time': '01/Dec/2023:23:34:30 +0000', 'timeEpoch': 1701473670081}, 'body': '{"update_id":147759353,\n"message":{"message_id":22,"from":{"id":5337682436,"is_bot":false,"first_name":"DuckyBlender","username":"DuckyBlender","language_code":"en"},"chat":{"id":5337682436,"first_name":"DuckyBlender","username":"DuckyBlender","type":"private"},"date":1701473670,"text":"https://www.google.com/search?client=firefox-b-d&q=crong","entities":[{"offset":0,"length":56,"type":"url"}]}}', 'isBase64Encoded': False}
    elif 'text' in body['message']:
        message = body['message']['text']
        if is_valid_url(message):
            short_url = shorten_url(message)
            #print(f"The short URL is: {short_url}")
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
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    response_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        'chat_id': body['message']['chat']['id'],
        'text': result
    }
    r = requests.post(response_url, json=payload)
    print(f"Response: {r.status_code}")
    return {
        "statusCode": 200,
    }
