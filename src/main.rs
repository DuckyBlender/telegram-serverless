use lambda_runtime::{service_fn, Error, LambdaEvent};
use serde_json::{Value, json};

#[tokio::main]
async fn main() -> Result<(), Error> {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .with_target(false)
        .without_time()
        .init();

    let func = service_fn(my_handler);
    lambda_runtime::run(func).await?;
    Ok(())
}

pub(crate) async fn my_handler(event: LambdaEvent<Value>) -> Result<Value, Error> {
    // Print the input request
    println!("Received request: {:?}", event.payload);

    // Return a 200 response with a simple message
    Ok(json!({ "status": 200 }))

}

#[cfg(test)]
mod tests {
    use crate::my_handler;
    use lambda_runtime::{Context, LambdaEvent};
    use serde_json::json;

    #[tokio::test]
    async fn response_is_status_200() {
        let context = Context::default();
        let payload = json!({ "any": "thing" });
        let event = LambdaEvent { payload, context };

        let result = my_handler(event).await.unwrap();

        assert_eq!(result, json!({ "status": 200 }));
    }
}