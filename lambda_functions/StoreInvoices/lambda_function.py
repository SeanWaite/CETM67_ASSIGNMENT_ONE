import json
import boto3
import os
import subprocess
from datetime import datetime

s3 = boto3.client('s3')
bucket = 'lwbespokeinvoices'
createPath = "/createinvoice"
downloadPath = "/download"


def lambda_handler(event, context):

    # Ensure calling method and api paths supplied are correct
    if event['httpMethod'] == "POST" and event['path'] == createPath:

        # Check to see if call is from test or other lambda.
        # If through api gateway need to use json.load
        try:
            fromLambdaFlag = event['from_lambda']
        except:
            fromLambdaFlag = False

        if fromLambdaFlag is False:
            loadedEvent = json.loads(event['body'])
        else:
            loadedEvent = event

        # html_string is required to create the pdf file
        try:
            html_string = loadedEvent['html_string']
        except KeyError:
            error_message = ('Missing html_string from request.')

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(error_message)
            return responseObject

        # forename is required to populate the pdf file
        try:
            forename = loadedEvent['forename']
        except:
            error_message = ('Missing forename from request.')

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(error_message)
            return responseObject

        # surname is required to populate the pdf file
        try:
            surname = loadedEvent['surname']
        except:
            error_message = ('Missing surname from request.')

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(error_message)
            return responseObject

        # The month and year of invoice is required to populate the pdf file
        try:
            yearMonth = loadedEvent['yearmonth']
        except:
            error_message = ('Missing yearmonth from request.')

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(error_message)
            return responseObject

        # Now we can check for the option wkhtmltopdf_options and map them to values. This is optional
        wkhtmltopdf_options = {}
        if 'wkhtmltopdf_options' in loadedEvent:
            if 'margin' in loadedEvent['wkhtmltopdf_options']:
                margins = loadedEvent['wkhtmltopdf_options']['margin'].split(' ')
                if len(margins) == 4:
                    wkhtmltopdf_options['margin-top'] = margins[0]
                    wkhtmltopdf_options['margin-right'] = margins[1]
                    wkhtmltopdf_options['margin-bottom'] = margins[2]
                    wkhtmltopdf_options['margin-left'] = margins[3]

            if 'orientation' in loadedEvent['wkhtmltopdf_options']:
                wkhtmltopdf_options['orientation'] = 'portrait'

                if loadedEvent['wkhtmltopdf_options']['orientation'].lower() == 'landscape':
                    wkhtmltopdf_options['orientation'] = 'landscape'

            if 'title' in loadedEvent['wkhtmltopdf_options']:
                wkhtmltopdf_options['title'] = loadedEvent['wkhtmltopdf_options']['title']

        # Write the HTML string to a tmp file
        dateTimeStamp = datetime.now()
        dateTimeString = dateTimeStamp.strftime("%Y%m%d%H%M%S")
        local_filename = f'/tmp/{forename}{surname}{yearMonth}-{dateTimeString}.html'
        upload_file = f'invoices/{forename}{surname}{yearMonth}-{dateTimeString}.pdf'

        # Delete any existing files with that name
        try:
            os.unlink(local_filename)
        except FileNotFoundError:
            pass

        with open(local_filename, 'w') as f:
            f.write(html_string)

        # Now we can create our command string to execute and upload the result to s3
        command = 'wkhtmltopdf  --load-error-handling ignore'  # ignore unecessary errors
        for key, value in wkhtmltopdf_options.items():
            if key == 'title':
                value = f'"{value}"'
            command += ' --{0} {1}'.format(key, value)
        command += ' {0} {1}'.format(local_filename, local_filename.replace('.html', '.pdf'))

        # Run the command
        subprocess.run(command, shell=True)

        # Upload the pdf
        s3.upload_file(Filename=local_filename.replace('.html', '.pdf'), Bucket=bucket, Key=upload_file)

        error_message = "Successfully created invoice"

        responseObject = {}
        responseObject['statusCode'] = '200'
        responseObject['headers'] = {}
        responseObject['body'] = "Call to create invoice was successful"
        return responseObject

    # Ensure calling method and api paths supplied are correct
    if event['httpMethod'] == "GET" and event['path'] == createPath:

        returnKeys = {}
        keyNumber = 1

        # Loop through bucket and only return files in the invoices folder
        for keys in s3.list_objects(Bucket=bucket)['Contents']:

            checkDir = keys['Key'].split('/')[0]

            try:
                checkFile = keys['Key'].split('/')[1]
            except:
                checkFile = None

            if checkDir == "invoices":
                if checkFile != "" or None:
                    returnKeys[f'Key{keyNumber}'] = {}
                    returnKeys[f'Key{keyNumber}']['Key'] = keys['Key']
                    keyNumber += 1

        responseObject = {}
        responseObject['statusCode'] = '200'
        responseObject['headers'] = {}
        responseObject['body'] = json.dumps(returnKeys)
        return responseObject

    # Ensure calling method and api paths supplied are correct
    if event['httpMethod'] == "GET" and event['path'] == downloadPath:

        # The object key is required to retrieve the pdf file
        try:
            objectKey = event['queryStringParameters']['key']
        except:
            error_message = ('Missing key from request.')

            responseObject = {}
            responseObject['statusCode'] = '400'
            responseObject['headers'] = {}
            responseObject['body'] = json.dumps(error_message)
            return responseObject

        response = s3.generate_presigned_url('get_object',
                                             Params={'Bucket': bucket,
                                                     'Key': f'invoices/{objectKey}'},
                                             ExpiresIn=120)

        responseObject = {}
        responseObject['statusCode'] = '200'
        responseObject['headers'] = {}
        responseObject['body'] = json.dumps(response)
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
