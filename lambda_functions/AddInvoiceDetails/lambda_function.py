import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

dynamo = boto3.resource("dynamodb")
table = dynamo.Table("InvoiceDetails")
invoicesPath = "/invoices"


def lambda_handler(event, context):

    # Ensure calling method and api paths supplied are correct
    if event['httpMethod'] == "POST" and event['path'] == invoicesPath:

        try:
            clientID = event['queryStringParameters']['clientid']
        except:
            message = "clientid field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        try:
            yearmonth = event['queryStringParameters']['yearmonth']
        except:
            message = "yearmonth field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        try:
            forename = event['queryStringParameters']['forename']
        except:
            message = "forename field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        try:
            surname = event['queryStringParameters']['surname']
        except:
            message = "surname field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        try:
            contactNumber = event['queryStringParameters']['number']
        except:
            message = "number field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        try:
            contactEmail = event['queryStringParameters']['email']
        except:
            message = "email field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        try:
            status = event['queryStringParameters']['status']
        except:
            message = "status field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        try:
            amount = event['queryStringParameters']['amount']
        except:
            message = "amount field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        floatAmount = Decimal(amount)

        response = table.put_item(Item={
            'client_id': clientID,
            'year_month': yearmonth,
            'forename': forename,
            'surname': surname,
            'phone_number': contactNumber,
            'email_address': contactEmail,
            'invoice_status': status,
            'amount': floatAmount
        })

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:

            # The below will called the StoreInvoices lambda to create the
            # invoice pdf from the data supplied
            lambda_client = boto3.client('lambda')
            inputToLambda = {}

            inputToLambda['httpMethod'] = 'POST'
            inputToLambda['path'] = '/createinvoice'
            inputToLambda['from_lambda'] = True
            inputToLambda['forename'] = forename
            inputToLambda['surname'] = surname
            inputToLambda['yearmonth'] = yearmonth
            inputToLambda['html_string'] = f'<!DOCTYPE html><html> \
                <head></head> \
                <body><h3>Invoice</h3><br><h6>Bill to:</h6> \
                <h6>{forename} {surname}</h6> \
                <h6>Please pay {floatAmount}</h6></body></html>'

            response = lambda_client.invoke(
                FunctionName='arn:aws:lambda:us-east-1:645243735875:function:StoreInvoices',
                InvocationType='RequestResponse',
                Payload=json.dumps(inputToLambda)
                )

            responseFromLambda = json.load(response['Payload'])

            if responseFromLambda['statusCode'] == "200":

                responseObject = {}
                responseObject['statusCode'] = '200'
                responseObject['headers'] = {}
                responseObject['body'] = "Call to insert and invoice creation was successful"
                return responseObject
            else:
                responseObject = {}
                responseObject['statusCode'] = responseFromLambda['statusCode']
                responseObject['headers'] = {}
                responseObject['body'] = "Call to insert and invoice creation failed"
                return responseObject
        else:
            responseObject = {}
            responseObject['statusCode'] = response['ResponseMetadata']['HTTPStatusCode']
            responseObject['headers'] = {}
            responseObject['body'] = "Call to insert query failed"

            return responseObject

    if event['httpMethod'] == "PATCH" and event['path'] == invoicesPath:

        try:
            clientID = event['queryStringParameters']['clientid']
        except:
            message = "clientid field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        try:
            yearMonth = event['queryStringParameters']['yearmonth']
        except:
            message = "yearmonth field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        try:
            updateTo = event['queryStringParameters']['updateto']
        except:
            message = "updateto field not supplied"

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(message)
            return responseObject

        # Update the status but on an existing record. DynamoDB would just
        # enter a new record if it does not already exist without the check
        try:
            response = table.update_item(
                Key={'client_id': clientID, 'year_month': yearMonth},
                ConditionExpression=Attr("client_id").exists() & Attr("year_month").exists(),
                UpdateExpression="set invoice_status=:statussupplied",
                ExpressionAttributeValues={':statussupplied': updateTo}
                )
        except ClientError as error:
            if error.response['Error']['Code'] == 'ConditionalCheckFailedException':
                responseObject = {}
                responseObject['statusCode'] = 400
                responseObject['headers'] = {}
                responseObject['body'] = "Supplied input does not exist. Failed to update invoice status"
                return responseObject

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:

            responseObject = {}
            responseObject['statusCode'] = '200'
            responseObject['headers'] = {}
            responseObject['body'] = "Successfully updated invoice status"

            return responseObject
        else:
            responseObject = {}
            responseObject['statusCode'] = response['ResponseMetadata']['HTTPStatusCode']
            responseObject['headers'] = {}
            responseObject['body'] = "Failed to update invoice status"

            return responseObject

    if event['httpMethod'] == "GET" and event['path'] == invoicesPath:

        allInvoices = table.scan()

        returnQueries = allInvoices['Items']

        # Require as can't return a Decimal type
        for amount in returnQueries:
            amount['amount'] = str(amount['amount'])

        responseObject = {}
        responseObject['statusCode'] = 200
        responseObject['headers'] = {}
        responseObject['body'] = json.dumps(returnQueries)
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
