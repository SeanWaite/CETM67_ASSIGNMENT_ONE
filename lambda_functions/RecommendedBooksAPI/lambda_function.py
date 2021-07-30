import json
import boto3
from boto3.dynamodb.conditions import Key

client = boto3.resource("dynamodb")
table = client.Table("Books")
bookPath = "/book"


def lambda_handler(event, context):

    # Ensure calling method and api paths supplied are correct
    if event['httpMethod'] == "GET" and event['path'] == bookPath:

        # Check age field has been supplied
        try:
            input_age = event['queryStringParameters']['age']
        except:
            message = "age field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        # Retrieve all books for that age group on the DB
        books = table.query(KeyConditionExpression=Key('age').eq(input_age))

        if books['Count'] == 0:
            message = "Sorry, no books are currently recommended for this age"

            responseObject = {}
            responseObject['statusCode'] = '200'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        returnBooks = books['Items']

        responseObject = {}
        responseObject['statusCode'] = 200
        responseObject['headers'] = {}
        responseObject['body'] = json.dumps(returnBooks)
        return responseObject

    # Ensure calling method and api paths supplied are correct
    if event['httpMethod'] == "POST" and event['path'] == bookPath:

        try:
            age = event['queryStringParameters']['age']
        except:
            message = "age field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        try:
            title = event['queryStringParameters']['title']
        except:
            message = "title field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        try:
            author = event['queryStringParameters']['author']
        except:
            message = "author field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        try:
            type = event['queryStringParameters']['type']
        except:
            message = "type field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        # Insert new books onto the DB with supplied inputs
        response = table.put_item(Item={
            'age': age,
            'title': title,
            'author': author,
            'type': type
        })

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            responseObject = {}
            responseObject['statusCode'] = '200'
            responseObject['headers'] = {}
            responseObject['body'] = "Call to insert new book was successful"
            return responseObject
        else:
            responseObject = {}
            responseObject['statusCode'] = response['ResponseMetadata']['HTTPStatusCode']
            responseObject['headers'] = {}
            responseObject['body'] = "Call to insert new book failed"
            return responseObject

    # Return error if called with correct method or path
    error = {}
    error["Code"] = "1"
    error["Message"] = "Invalid API Call"

    responseObject = {}
    responseObject['statusCode'] = 400
    responseObject['headers'] = {}
    responseObject['body'] = json.dumps(error)
    return responseObject
