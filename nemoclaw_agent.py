# WhatsApp Bot Code

# This is an example code for a simple WhatsApp bot.
import os
from twilio.rest import Client

# Your Twilio credentials
account_sid = os.environ['TWILIO_ACCOUNT_SID']
token = os.environ['TWILIO_AUTH_TOKEN']
from_number = os.environ['TWILIO_PHONE_NUMBER']

client = Client(account_sid, token)

def send_whatsapp_message(to, message):
    message = client.messages.create(
        body=message,
        from_=f'whatsapp:{from_number}',
        to=f'whatsapp:{to}'
    )
    return message.sid

# Example usage
if __name__ == '__main__':
    recipient = '+1234567890'
    msg = 'Hello from your WhatsApp bot!'
    message_sid = send_whatsapp_message(recipient, msg)
    print(f'Message sent with SID: {message_sid}')