import boto3
from botocore.exceptions import ClientError
from recreation_gov_client import RecreationGovClient
from dateutil.relativedelta import relativedelta
from date_time_utils import to_human_readable_dt_format

from campground_ids import CAMPSITE_ID_TO_PARK_DISPLAY_NAME
from test_campgrounds_ids import TEST_CAMPSITE_ID_TO_PARK_DISPLAY_NAME


class EmailClient:

    def __init__(cls, is_test_mode):
        cls.is_test_mode = is_test_mode

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
        return "<a href='" + RecreationGovClient.CAMPSITE_RESERVATION_URL.format(campsite_id=campsite_id) + "'>" + campsite_id + "</a>"

    @classmethod
    def build_headline(cls):
        subject = "<html><body><h1>Do you smell the pine cones yet?</h1>" \
                  "<p>Here are some available campsites. Book now!</p>"
        return subject

    def build_html_body(cls, availability):
        body_html = cls.build_headline()
        for park_id in availability:
            if cls.is_test_mode:
                body_html += "<h2>" + TEST_CAMPSITE_ID_TO_PARK_DISPLAY_NAME.get(park_id) + "</h2>"
            else:
                body_html += "<h2>" + CAMPSITE_ID_TO_PARK_DISPLAY_NAME.get(park_id) + "</h2>"
            # let's build a map of available_day -> [ campsite_ids ]
            available_days_to_campsite = {}
            campsite_id_to_available_days = availability.get(park_id)

            for campsite_id in campsite_id_to_available_days:
                for day in campsite_id_to_available_days.get(campsite_id):
                    available_days_to_campsite.setdefault(day, []).append(campsite_id)

            for day in available_days_to_campsite:
                available_days_to_campsite.get(day).sort()

            available_days_to_campsite_sorted_by_day = dict(sorted(available_days_to_campsite.items()))

            body_html += "<ul>"

            for day in available_days_to_campsite_sorted_by_day:
                body_html += "<li>" + to_human_readable_dt_format(day) + " - " + to_human_readable_dt_format(
                    day + relativedelta(days=2))
                body_html += "<ul>"
                campsite_list = available_days_to_campsite_sorted_by_day.get(day)

                # Limit campsites to 5 per weekend for better display purposes
                if len(campsite_list) > 5:
                    campsite_list = campsite_list[0:5]

                for campsite_id in campsite_list:
                    body_html += "<li>" + cls.get_reservation_link(campsite_id) + "</li>"
                body_html += "</ul>"
                body_html += "</li>"

            body_html += "</ul>"

        body_html += "</body></html>"
        return body_html

    def send_email(cls, weekend_availability, contiguous_availability):
        subject = "[TEST]" if cls.is_test_mode else ""
        if weekend_availability:
            print("Got weekend availability {}", weekend_availability)
            subject += "Snoop camp smells some available campsites (weekends)"
            body_html = cls.build_html_body(weekend_availability)
        elif contiguous_availability:
            print("Got contiguous availability {}", contiguous_availability)
            subject += "Snoop camp smells some available campsites (non weekend)"
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
                        "shgar.gir@gmail.com" if cls.is_test_mode else cls.RECIPIENT,
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
                Source="shgar.gir@gmail.com" if cls.is_test_mode else cls.SENDER
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