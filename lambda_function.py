import json
import boto3  # This is the AWS library

def lambda_handler(event, context):
    # 1. These are the boxes (variables) to hold our data
    metric_name = "Impressions"
    publisher = "SportsStream_HD"
    threshold_drop = 15  # Percent drop we care about
    
    # 2. This is a basic "If" statement (Logic)
    # We will eventually tell the AI to fill these in!
    current_drop = 20 

    if current_drop > threshold_drop:
        status = "🚨 ANOMALY"
        message = f"Drop detected on {publisher}. Under-delivering on live game!"
    else:
        status = "✅ NORMAL"
        message = "Delivery is on track."

    print(message) # This shows up in our logs
    
    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }