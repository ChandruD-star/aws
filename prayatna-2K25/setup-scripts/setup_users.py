import boto3
import json
import smtplib
from email.mime.text import MIMEText

# AWS Configuration
AWS_REGION = "us-east-1"

# SMTP Configuration (Replace with your SMTP provider details)
SMTP_SERVER = "smtp.gmail.com"  # Change this to your mail server (e.g., smtp.gmail.com)
SMTP_PORT = 587  # Use 465 for SSL or 587 for TLS
SMTP_USERNAME = "noreply@gmail.com"  # Replace with your noreply email
SMTP_PASSWORD = "xxxxxxxxxxxxxxxxxxxxxxxxx"  # Replace with the SMTP password or App Password

# Permissions Policy for IAM users (Allow API Gateway, Lambda, DynamoDB, but deny AWS Console)
IAM_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Deny",
            "Action": "iam:CreateLoginProfile",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "apigateway:*",
                "s3:*",
                "lambda:*",
                "dynamodb:*"
            ],
            "Resource": "*"
        }
    ]
}

# Initialize AWS IAM client
iam_client = boto3.client("iam")

# Read recipient emails from a file
def get_recipients(filename):
    with open(filename, "r") as file:
        return [line.strip() for line in file if line.strip()]

# Create IAM user, attach policy, and generate access keys
def create_iam_user(email):
    username = email.replace("@", "_").replace(".", "_")  # Convert email to a valid IAM username
    try:
        # Create IAM User
        iam_client.create_user(UserName=username)

        # Attach policy to user
        iam_client.put_user_policy(
            UserName=username,
            PolicyName="LimitedPermissions",
            PolicyDocument=json.dumps(IAM_POLICY)
        )

        # Create Access Keys
        access_keys = iam_client.create_access_key(UserName=username)

        return {
            "Username": username,
            "AccessKeyId": access_keys["AccessKey"]["AccessKeyId"],
            "SecretAccessKey": access_keys["AccessKey"]["SecretAccessKey"]
        }
    except Exception as e:
        print(f"Error creating IAM user for {email}: {e}")
        return None

# Send email using SMTP
def send_email(email, credentials):
    subject = "Your AWS IAM Credentials"
    body = f"""
    Hello,

    Your AWS IAM user has been created successfully for AWS Cloud Workshop. Below are your credentials:

    IAM Username: {credentials['Username']}
    AWS Access Key ID: {credentials['AccessKeyId']}
    AWS Secret Access Key: {credentials['SecretAccessKey']}

    To configure AWS CLI, run the following command:
    
    aws configure set aws_access_key_id {credentials['AccessKeyId']}
    aws configure set aws_secret_access_key {credentials['SecretAccessKey']}
    aws configure set region {AWS_REGION}
    
    Please do not share these credentials with anyone and this accesswill be deleted after the workshop.

    Best Regards,
    AWS Admin
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USERNAME
    msg["To"] = email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure connection
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, email, msg.as_string())
        print(f"Email sent successfully to {email}")
    except Exception as e:
        print(f"Error sending email to {email}: {e}")

if __name__ == "__main__":
    recipients = get_recipients("recipients.txt")
    for email in recipients:
        credentials = create_iam_user(email)
        if credentials:
            send_email(email, credentials)
