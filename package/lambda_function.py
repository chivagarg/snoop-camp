import boto3
from botocore.exceptions import ClientError
import json
import requests
from dateutil import rrule
import datetime

import logging

import requests
import user_agent

LOG = logging.getLogger(__name__)


class RecreationGovClient:

    BASE_URL = "https://www.recreation.gov"
    AVAILABILITY_ENDPOINT = (
        BASE_URL + "/api/camps/availability/campground/{park_id}/month"
    )
    MAIN_PAGE_ENDPOINT = BASE_URL + "/api/camps/campgrounds/{park_id}"

    #headers = {"User-Agent": user_agent.generate_user_agent() }
    
    @classmethod
    def get_availability(cls, park_id, month_date):
        LOG.debug(
            "Querying for {} with these params: {}".format(park_id, params)
        )
        url = cls.AVAILABILITY_ENDPOINT.format(park_id=park_id)
        resp = cls._send_request(url, params)
        return resp

    @classmethod
    def get_park_name(cls, park_id):
        resp = cls._send_request(
            cls.MAIN_PAGE_ENDPOINT.format(park_id=park_id), {}
        )
        return resp["campground"]["facility_name"]

    @classmethod
    def _send_request(cls, url, params):
        resp = requests.get(url, params=params, headers=cls.headers)
        if resp.status_code != 200:
            raise RuntimeError(
                "failedRequest",
                "ERROR, {status_code} code received from {url}: {resp_text}".format(
                    status_code=resp.status_code, url=url, resp_text=resp.text
                ),
            )
        return resp.json()


def send_email(sender, recipient, skip_email=True):
    
    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the 
    #ConfigurationSetName=CONFIGURATION_SET argument below.
    #CONFIGURATION_SET = "ConfigSet"

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-west-2"

    # The subject line for the email.
    SUBJECT = "Amazon SES Test (SDK for Python)"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Amazon SES Test (Python)\r\n"
                 "This email was sent with Amazon SES using the "
                 "AWS SDK for Python (Boto)."
                )
            
    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
      <h1>Amazon SES Test (SDK for Python)</h1>
      <p>This email was sent with
        <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
        <a href='https://aws.amazon.com/sdk-for-python/'>
          AWS SDK for Python (Boto)</a>.</p>
    </body>
    </html>
                """            
    
    # The character encoding for the email.
    CHARSET = "UTF-8"
    
    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)
    
    if skip_email:
        print("Dry run mode. Email send skipped!")
        return False
    
    sent = False

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    recipient,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=sender,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong. 
    except ClientError as e:
        print(e.response['Error']['Message'])
        return False
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
        return True


def lambda_handler(event, context):
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "chivagarg@gmail.com"

    # Replace recipient@example.com with a "To" address. If your account 
    # is still in the sandbox, this address must be verified.
    RECIPIENT = "shgar.gir@gmail.com"


    email_sent = send_email(sender=SENDER, recipient=RECIPIENT, skip_email=True)

        
    if email_sent:
        return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda Successful!')
        }
    return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda Email not sent!')
        }
