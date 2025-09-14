import boto3, json, os

TABLE_NAME = os.environ['TABLE_NAME']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    try:
        # Get shortId from path parameters
        short_id = None
        if event.get('pathParameters'):
            short_id = event['pathParameters'].get('shortId')

        if not short_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "shortId missing in path"})
            }

        # Fetch from DynamoDB
        resp = table.get_item(Key={"shortId": short_id})
        item = resp.get('Item')
        if not item:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Short URL not found"})
            }

        long_url = item.get('longUrl')

        # Increment hits counter (optional)
        try:
            table.update_item(
                Key={"shortId": short_id},
                UpdateExpression="SET hits = if_not_exists(hits, :zero) + :inc",
                ExpressionAttributeValues={":inc": 1, ":zero": 0}
            )
        except Exception:
            pass

        # Redirect user
        return {
            "statusCode": 301,
            "headers": {
                "Location": long_url
            }
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
