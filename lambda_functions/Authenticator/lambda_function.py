# Simple authenticator function so token is required to access API's which use it
def lambda_handler(event, context):

    auth = 'Deny'

    if event['authorizationToken'] == 'cetm67_test':
        auth = 'Allow'

    authResponse = {}
    authResponse['principalId'] = "cetm67_test"
    authResponse['policyDocument'] = {}
    authResponse['policyDocument']['Version'] = "2012-10-17"
    authResponse['policyDocument']['Statement'] = {}
    authResponse['policyDocument']['Statement']['Action'] = "execute-api:Invoke"
    authResponse['policyDocument']['Statement']['Resource'] = "arn:aws:execute-api:us-east-1:645243735875:*/*/*"
    authResponse['policyDocument']['Statement']['Effect'] = auth

    return authResponse
