import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.conditions import Attr
from datetime import datetime

dynamo = boto3.resource("dynamodb")
table = dynamo.Table("BusinessQueries")
queryPath = "/query"
countQueriesPath = "/countqueries"
allQueriesPath = "/allqueries"
retreieveOldestPath = "/retrieveoldest"


def lambda_handler(event, context):

    # Ensure calling method and api paths supplied are correct
    if event['httpMethod'] == "POST" and event['path'] == queryPath:

        dateTimeStamp = datetime.now()
        dateTimeString = dateTimeStamp.strftime("%Y%m%d%H%M%S")

        # forename is required
        try:
            forename = event['queryStringParameters']['forename']
        except:
            error_message = ('Missing forename from request.')

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(error_message)
            return responseObject

        # surname is required
        try:
            surname = event['queryStringParameters']['surname']
        except:
            error_message = ('Missing surname from request.')

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(error_message)
            return responseObject

        # number is required
        try:
            contactNumber = event['queryStringParameters']['number']
        except:
            error_message = ('Missing number from request.')

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(error_message)
            return responseObject

        # email is required
        try:
            contactEmail = event['queryStringParameters']['email']
        except:
            error_message = ('Missing email from request.')

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(error_message)
            return responseObject

        # message is required
        try:
            message = event['queryStringParameters']['message']
        except:
            error_message = ('Missing message from request.')

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(error_message)
            return responseObject

        # answered needs to be a boolean but is recieved as a string so below is required
        try:
            if event['queryStringParameters']['answered'].upper() == "TRUE":
                answered = True
            else:
                answered = False
        except:
            message = "updateto field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        # Create unique query ID
        queryID = contactEmail.partition("@")[0] + dateTimeString

        # Insert query into DynamoDB table
        response = table.put_item(Item={
            'query_id': queryID,
            'date_added': dateTimeString,
            'forename': forename,
            'surname': surname,
            'phone_number': contactNumber,
            'email_address': contactEmail,
            'message': message,
            'answered': answered
        })

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:

            # If successful send email to staff to let them know a new query has been asked
            # For the purposes of my assignment this is my university email address
            sns_client = boto3.client('sns')
            sns_subject = "New query - " + queryID
            sns_message = "New query recieved from " + forename + " " + surname + "\n" + message

            sns_client.publish(TopicArn='arn:aws:sns:us-east-1:645243735875:QueryNotificaton',
                               Message=sns_message,
                               Subject=sns_subject)

            responseObject = {}
            responseObject['statusCode'] = '200'
            responseObject['headers'] = {}
            responseObject['body'] = "Call to insert query was successful"
            return responseObject
        else:
            responseObject = {}
            responseObject['statusCode'] = response['ResponseMetadata']['HTTPStatusCode']
            responseObject['headers'] = {}
            responseObject['body'] = "Call to insert query failed"
            return responseObject

    # Ensure calling method and api paths supplied are correct
    if event['httpMethod'] == "PATCH" and event['path'] == queryPath:

        # queryid is required
        try:
            queryID = event['queryStringParameters']['queryid']
        except:
            message = "queryid field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        # updateto needs to be a boolean but is recieved as a string so below is required
        try:
            if event['queryStringParameters']['updateto'].upper() == "TRUE":
                updateTo = True
            else:
                updateTo = False
        except:
            message = "updateto field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        # Update query to say if answered or not, but only if queryid already exists
        try:
            response = table.update_item(
                Key={'query_id': queryID},
                ConditionExpression=Attr("query_id").exists(),
                UpdateExpression="set answered=:bool",
                ExpressionAttributeValues={':bool': updateTo}
                )
        except ClientError as error:
            if error.response['Error']['Code'] == 'ConditionalCheckFailedException':
                responseObject = {}
                responseObject['statusCode'] = 400
                responseObject['headers'] = {}
                responseObject['body'] = "Supplied input does not exist. Failed to update query status"
                return responseObject

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:

            responseObject = {}
            responseObject['statusCode'] = '200'
            responseObject['headers'] = {}
            responseObject['body'] = "Successfully updated query"
            return responseObject
        else:
            responseObject = {}
            responseObject['statusCode'] = response['ResponseMetadata']['HTTPStatusCode']
            responseObject['headers'] = {}
            responseObject['body'] = "Failed to update query"
            return responseObject

    # Ensure calling method and api paths supplied are correct
    if event['httpMethod'] == "GET" and event['path'] == countQueriesPath:

        # Count how many queries are answered and outstanding
        countAnswered = table.scan(FilterExpression=Key('answered').eq(True),
                                   Select='COUNT')
        countOutstanding = table.scan(FilterExpression=Key('answered').eq(False),
                                      Select='COUNT')

        message = {}
        message['answered'] = countAnswered['Count']
        message['outstanding'] = countOutstanding['Count']

        responseObject = {}
        responseObject['statusCode'] = 200
        responseObject['headers'] = {}
        responseObject['body'] = json.dumps(message)
        return responseObject

    # Ensure calling method and api paths supplied are correct
    if event['httpMethod'] == "GET" and event['path'] == allQueriesPath:

        # Scan for all queries on DB
        allQueries = table.scan()

        returnQueries = allQueries['Items']

        responseObject = {}
        responseObject['statusCode'] = 200
        responseObject['headers'] = {}
        responseObject['body'] = json.dumps(returnQueries)
        return responseObject

    # Ensure calling method and api paths supplied are correct
    if event['httpMethod'] == "GET" and event['path'] == retreieveOldestPath:

        # Scan for all outstanding queries so the oldest can be answered first
        outstanding = table.scan(FilterExpression=Key('answered').eq(False))
        queryNo = 1
        oldestQuery = {}

        # Loop through all returned queries and check the dates to only return the oldest
        for query in outstanding['Items']:
            if queryNo == 1:
                oldestQuery['query_id'] = query['query_id']
                oldestQuery['date_added'] = query['date_added']
                oldestQuery['forename'] = query['forename']
                oldestQuery['surname'] = query['surname']
                oldestQuery['phone_number'] = query['phone_number']
                oldestQuery['email_address'] = query['email_address']
                oldestQuery['message'] = query['message']
            else:
                if query['date_added'] < oldestQuery['date_added']:
                    oldestQuery['query_id'] = query['query_id']
                    oldestQuery['date_added'] = query['date_added']
                    oldestQuery['forename'] = query['forename']
                    oldestQuery['surname'] = query['surname']
                    oldestQuery['phone_number'] = query['phone_number']
                    oldestQuery['email_address'] = query['email_address']
                    oldestQuery['message'] = query['message']

            queryNo += 1

        responseObject = {}
        responseObject['statusCode'] = 200
        responseObject['headers'] = {}
        responseObject['body'] = json.dumps(oldestQuery)
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
