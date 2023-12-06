use lambda_runtime::{handler_fn, Context, Error};
use reqwest::Client;
use reqwest::header::AUTHORIZATION;
use reqwest::multipart;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::{env, fs::{File, self}, io::{Read, Write}};

#[derive(Deserialize)]
struct LambdaInput {
    body: String,
}

#[derive(Serialize)]
struct LambdaOutput {
    statusCode: u16,
    body: String,
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    let handler = handler_fn(func);
    lambda_runtime::run(handler).await?;
    Ok(())
}

async fn func(event: LambdaInput, _context: Context) -> Result<LambdaOutput, Error> {
    let body: Value = serde_json::from_str(&event.body)?;

    // Check if the message is a voice message
    if body["message"]["voice"].is_null() {
        return Ok(LambdaOutput {
            statusCode: 200,
            body: "Not a voice message".to_string(),
        });
    } else {
        // Save it to /tmp/file_id.ogg
        let file_id = body["message"]["voice"]["file_id"].as_str().unwrap();
        let file_path = download_audio(file_id).await?;
        // The file has been downloaded to /tmp/file_id.ogg
        // Now send it to OpenAI Whisper
        let openai_key = env::var("OPENAI_KEY").unwrap();
        //   curl https://api.openai.com/v1/audio/transcriptions \
        //      -H "Authorization: Bearer $OPENAI_API_KEY" \
        //      -H "Content-Type: multipart/form-data" \
        //      -F file="@/path/to/file/audio.mp3" \
        //      -F model="whisper-1"

        // Open the file to send
        let client = Client::new();

        let model = "whisper-1";
        let form = multipart::Form::new()
        .text("model", model.to_string())
        .text("response_format", "text".to_string())
        .part("file", multipart::Part::bytes(fs::read(file_path).unwrap()).file_name("audio.ogg").mime_str("audio/ogg").unwrap());
    
        let response = client
            .post("https://api.openai.com/v1/audio/transcriptions")
            .header("Authorization", format!("Bearer {}", openai_key))
            .multipart(form)
            .send()
            .await?;

            // Check if the request was successful and print the response
    if response.status().is_success() {
        // nice
    } else {
        // not nice
        return Ok(LambdaOutput {
            statusCode: 400,
            body: "Error sending audio to OpenAI Whisper".to_string(),
        });
    }

        // Get the response
        let text = response.text().await?;
        println!("Response: {:?}", text);

        // Send the response to Telegram
        let telegram_token = env::var("TELEGRAM_TOKEN").unwrap();
        let chat_id = body["message"]["chat"]["id"].as_i64().unwrap();
        let url = format!(
            "https://api.telegram.org/bot{}/sendMessage",
            telegram_token
        );

        let payload = json!({
            "chat_id": chat_id,
            "text": text,
        });

        let response = reqwest::Client::new()
            .post(&url)
            .json(&payload)
            .send()
            .await?;


    // Check if the request was successful and print the response
    if response.status().is_success() {
        println!("Response: {:?}", response.text().await.unwrap());
    } else {
        println!("Error: {:?}", response.text().await.unwrap());
    }

        return Ok(LambdaOutput {
            statusCode: 200,
            body: "Voice message transcription sent!".to_string(),
        });
    }
}

fn is_valid_url(url: &str) -> bool {
    url::Url::parse(url).is_ok()
}

async fn download_audio(file_id: &str) -> Result<String, Error> {
    let telegram_token = env::var("TELEGRAM_TOKEN").unwrap();
    let url = format!(
        "https://api.telegram.org/bot{}/getFile?file_id={}",
        telegram_token, file_id
    );
    let resp = reqwest::get(&url).await?.json::<Value>().await?;
    let file_path = resp["result"]["file_path"].as_str().unwrap();
    let file_url = format!(
        "https://api.telegram.org/file/bot{}/{}",
        telegram_token, file_path
    );
    let file_name = file_path.split("/").last().unwrap();
    let file_path = format!("/tmp/{}", file_name);
    let mut file = File::create(&file_path)?;
    let mut resp = reqwest::get(&file_url).await?;
    while let Some(chunk) = resp.chunk().await? {
        file.write_all(&chunk)?;
    }
    Ok(file_path)
}
