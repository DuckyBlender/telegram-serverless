use lambda_runtime::{handler_fn, Context, Error};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::env;

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

    // Example of processing a message with a URL
    if let Some(message) = body["message"]["text"].as_str() {
        if is_valid_url(message) {
            let short_url = shorten_url(message).await?;
            Ok(LambdaOutput {
                statusCode: 200,
                body: serde_json::to_string(&short_url)?,
            })
        } else {
            Ok(LambdaOutput {
                statusCode: 200,
                body: "Not a valid URL.".to_string(),
            })
        }
    } else {
        Ok(LambdaOutput {
            statusCode: 200,
            body: "Not a valid message.".to_string(),
        })
    }
}

fn is_valid_url(url: &str) -> bool {
    // Implement URL validation logic or use a crate like `url`
    url::Url::parse(url).is_ok()
}

async fn shorten_url(url: &str) -> Result<String, Error> {
    let client = reqwest::Client::new();
    let bitly_token = env::var("BITLY_ACCESS_TOKEN")?;
    let response = client
        .post("https://api-ssl.bitly.com/v4/shorten")
        .header("Authorization", format!("Bearer {}", bitly_token))
        .json(&serde_json::json!({
            "long_url": url,
            "domain": "bit.ly",
        }))
        .send()
        .await?;

    if response.status_code() == reqwest::StatusCode::TOO_MANY_REQUESTS {
        return Err(Error::from("Bitly API rate limit exceeded."));
    }

    let json = response.json::<Value>().await?;
    Ok(json["id"].as_str().unwrap_or_default().to_string())
}

// Implement `download_audio` and `process_audio` functions similarly