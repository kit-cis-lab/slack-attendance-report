import json


def handler(event, context):
    print("Lambda function invoked!")
    return {"statusCode": 200, "body": json.dumps("Hello from Lambda!")}
