from twilio.rest import Client
import random

# Twilio credentials
account_sid = "ACfb2e9d76da8709d16651db3a409e71ae"
auth_token = "46e2d17a0a26befc2146e664ca8d606a"
twilio_phone_number = "+12057749667"


# Function to generate a random OTP
def generate_otp():
    return str(random.randint(1000, 9999))


# Function to send OTP via Twilio
def send_otp_via_twilio(to_phone_number, otp):
    client = Client(account_sid, auth_token)

    message_body = f"Your OTP is: {otp}"

    message = client.messages.create(
        body=message_body,
        from_=twilio_phone_number,
        to=to_phone_number
    )

    return message.sid


# Example: Send OTP to a phone number
phone_number = "+917092110114"  # Replace with the recipient's phone number
otp = generate_otp()

# Send OTP
message_sid = send_otp_via_twilio(phone_number, otp)

print(f"OTP sent successfully. Message SID: {message_sid}")
