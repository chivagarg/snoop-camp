import boto3
from botocore.exceptions import ClientError
from recreation_gov_client import RecreationGovClient

from campground_ids import CAMPSITE_ID_TO_PARK_DISPLAY_NAME


class EmailClient:
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "snoop-campers@googlegroups.com"

    # Replace recipient@example.com with a "To" address. If your account
    # is still in the sandbox, this address must be verified.
    RECIPIENT = "snoop-campers@googlegroups.com"

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    # CONFIGURATION_SET = "ConfigSet"
    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-west-2"

    # The character encoding for the email.
    CHARSET = "UTF-8"

    @classmethod
    def get_reservation_link(cls, campsite_id):
        return "<a href='" + RecreationGovClient.CAMPSITE_RESERVATION_URL.format(campsite_id=campsite_id) + "'> Reserve</a>"

    @classmethod
    def build_html_body(cls, availability):
        body_html = "<html><body><h1>Do you smell the pine cones yet?</h1>" \
                    "<p>Here are some available campsites. Each bullet point represents a particular campsite within a" \
                    " park and lists contiguous 2 days (e.g. Friday & Saturday) that the campsite is free. Book now!</p>"
        for park_id in availability:
            body_html += "<h2>" + CAMPSITE_ID_TO_PARK_DISPLAY_NAME.get(park_id) + "</h2>"
            campsite_id_to_available_day = availability.get(park_id)
            body_html += "<ul>"
            for available_campsite_id in campsite_id_to_available_day:
                available_days = campsite_id_to_available_day.get(available_campsite_id)
                available_days_as_str = ','.join(available_days)
                body_html += "<li>" + available_days_as_str + cls.get_reservation_link(available_campsite_id) + "</li>"
            body_html += "</ul>"
        body_html += "</body></html>"
        return body_html

    @classmethod
    def send_email(cls, weekend_availability, contiguous_availability):
        if weekend_availability:
            print("Got weekend availability {}", weekend_availability)
            subject = "Snoop camp smells some available campsites (weekend)"
            body_html = cls.build_html_body(weekend_availability)
        elif contiguous_availability:
            print("Got contiguous availability {}", contiguous_availability)
            subject = "Snoop camp smells some available campsites (non weekend)"
            # The HTML body of the email.
            body_html = cls.build_html_body(contiguous_availability)
        else:
            raise Exception('We should not even be here!')

        # The email body for recipients with non-HTML email clients.
        body_text = ("Hello from snoop camp\r\n"
                     "I found some campsites of interest for you!")

        # Create a new SES resource and specify a region.
        client = boto3.client('ses', region_name=cls.AWS_REGION)

        # Try to send the email.
        try:
            # Provide the contents of the email.
            response = client.send_email(
                Destination={
                    'ToAddresses': [
                        cls.RECIPIENT,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': cls.CHARSET,
                            'Data': body_html,
                        },
                        'Text': {
                            'Charset': cls.CHARSET,
                            'Data': body_text,
                        },
                    },
                    'Subject': {
                        'Charset': cls.CHARSET,
                        'Data': subject,
                    },
                },
                Source=cls.SENDER,
                # If you are not using a configuration set, comment or delete the
                # following line
                # ConfigurationSetName=CONFIGURATION_SET,
            )
        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response['Error']['Message'])
            return False
        else:
            print("Email sent successfully! Message ID:"),
            print(response['MessageId'])
            return True