// This example requires the following input to succeed:
// { "command": "do something" }

use lambda_runtime::{service_fn, Error, LambdaEvent};
use serde::{Deserialize, Serialize};
use tracing::info;


#[derive(Serialize)]
struct LambdaResponse {
    req_id: String,
    msg: String,
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    // required to enable CloudWatch error logging by the runtime
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        // disable printing the name of the module in every log line.
        .with_target(false)
        // disabling time is handy because CloudWatch will add the ingestion time.
        .without_time()
        .init();

    let func = service_fn(my_handler);
    lambda_runtime::run(func).await?;
    Ok(())
}

pub(crate) async fn my_handler(event: LambdaEvent<String>) -> Result<LambdaResponse, Error> {
    // convert to json
    let json = serde_json::to_string(&event.payload).unwrap();

    // print the json to stdout
    info!("Received event: {}", json);

    // Check if message has URL or audio
    // This is example request for a message with audio
    // {'version': '2.0', 'routeKey': 'POST /duckShortenerTelegram', 'rawPath': '/duckShortenerTelegram', 'rawQueryString': '', 'headers': {'accept-encoding': 'gzip, deflate', 'content-length': '633', 'content-type': 'application/json', 'host': 'qb76wpzrm8.execute-api.eu-central-1.amazonaws.com', 'x-amzn-trace-id': 'Root=1-656f9d06-45b6d8ba54ac568411629b53', 'x-forwarded-for': '91.108.6.95', 'x-forwarded-port': '443', 'x-forwarded-proto': 'https'}, 'requestContext': {'accountId': '534406734576', 'apiId': 'qb76wpzrm8', 'domainName': 'qb76wpzrm8.execute-api.eu-central-1.amazonaws.com', 'domainPrefix': 'qb76wpzrm8', 'http': {'method': 'POST', 'path': '/duckShortenerTelegram', 'protocol': 'HTTP/1.1', 'sourceIp': '91.108.6.95', 'userAgent': ''}, 'requestId': 'PfV5EhsJFiAEJqg=', 'routeKey': 'POST /duckShortenerTelegram', 'stage': '$default', 'time': '05/Dec/2023:21:58:30 +0000', 'timeEpoch': 1701813510505}, 'body': '{"update_id":147759372,\n"message":{"message_id":50,"from":{"id":5337682436,"is_bot":false,"first_name":"DuckyBlender","username":"DuckyBlender","language_code":"en"},"chat":{"id":5337682436,"first_name":"DuckyBlender","username":"DuckyBlender","type":"private"},"date":1701813510,"forward_from":{"id":6442355191,"is_bot":false,"first_name":"Mloda","last_name":"Alchimiczka","username":"Alchimiczka","language_code":"en"},"forward_date":1701799632,"voice":{"duration":24,"mime_type":"audio/ogg","file_id":"AwACAgQAAxkBAAMyZW-dBiH0AAHwICKISxifj-dcnDGOAAJwEQACl_aBUzgXY_cj1hcaMwQ","file_unique_id":"AgADcBEAApf2gVM","file_size":94966}}}', 'isBase64Encoded': False}
    // This is example request for a message with URL
    // # {'version': '2.0', 'routeKey': 'POST /duckShortenerTelegram', 'rawPath': '/duckShortenerTelegram', 'rawQueryString': '', 'headers': {'accept-encoding': 'gzip, deflate', 'content-length': '398', 'content-type': 'application/json', 'host': 'qb76wpzrm8.execute-api.eu-central-1.amazonaws.com', 'x-amzn-trace-id': 'Root=1-656a6d86-4553121c13ba59c308e77f47', 'x-forwarded-for': '91.108.6.95', 'x-forwarded-port': '443', 'x-forwarded-proto': 'https'}, 'requestContext': {'accountId': '534406734576', 'apiId': 'qb76wpzrm8', 'domainName': 'qb76wpzrm8.execute-api.eu-central-1.amazonaws.com', 'domainPrefix': 'qb76wpzrm8', 'http': {'method': 'POST', 'path': '/duckShortenerTelegram', 'protocol': 'HTTP/1.1', 'sourceIp': '91.108.6.95', 'userAgent': ''}, 'requestId': 'PSYM_i61FiAEPoA=', 'routeKey': 'POST /duckShortenerTelegram', 'stage': '$default', 'time': '01/Dec/2023:23:34:30 +0000', 'timeEpoch': 1701473670081}, 'body': '{"update_id":147759353,\n"message":{"message_id":22,"from":{"id":5337682436,"is_bot":false,"first_name":"DuckyBlender","username":"DuckyBlender","language_code":"en"},"chat":{"id":5337682436,"first_name":"DuckyBlender","username":"DuckyBlender","type":"private"},"date":1701473670,"text":"https://www.google.com/search?client=firefox-b-d&q=crong","entities":[{"offset":0,"length":56,"type":"url"}]}}', 'isBase64Encoded': False}
    

    // prepare the response
    let resp = LambdaResponse {
        req_id: event.context.request_id,
        msg: format!("Command test executed."),
    };

    // return `Response` (it will be serialized to JSON automatically by the runtime)
    Ok(resp)
}

// #[cfg(test)]
// mod tests {
//     use crate::{my_handler, LambdaRequest};
//     use lambda_runtime::{Context, LambdaEvent};

//     #[tokio::test]
//     async fn response_is_good_for_simple_input() {
//         let id = "ID";

//         let mut context = Context::default();
//         context.request_id = id.to_string();

//         let payload = LambdaRequest {
//             command: "X".to_string(),
//         };
//         let event = LambdaEvent { payload, context };

//         let result = my_handler(event).await.unwrap();

//         assert_eq!(result.msg, "Command X executed.");
//         assert_eq!(result.req_id, id.to_string());
//     }
// }
