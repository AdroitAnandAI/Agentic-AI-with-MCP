from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from mcp import types
import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

# Initialize FastMCP server
mcp = FastMCP("gmail")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@mcp.tool()
def send_email(
    subject="Ramblings from Tele-Agent",
    body="This is a default email body.",
    sheet_url: str = None
) -> str:
    """
    Sends mail or email to gmail using SMTP.
    
    Args:
        subject (str): Email subject. Default: "Computed Result using MCP".
        body (str): Plain text email body.
        sheet_url (str): URL of the Google Sheet to include in the email (optional).
    """
    # Configuration
    to_email = "anandsharespace@gmail.com"
    from_email = "anandsharespace@gmail.com"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    load_dotenv()
    password = os.getenv("GMAIL_OAUTH_KEY")
    # print(f"password: {password}")

    # Create message
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Prepare email body
    email_body = ""
    if sheet_url:
        email_body += f"\n\nYou can view the results in the Google Sheet here: {sheet_url}"
    
    msg.attach(MIMEText(email_body, "plain"))

    # Enhanced error handling
    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.set_debuglevel(1)  # Enable SMTP protocol logging
            logger.info("Connecting to server...")
            server.starttls()
            logger.info("TLS started. Attempting login...")
            server.login(from_email, password)
            logger.info("Login successful. Sending email...")
            server.send_message(msg)
            logger.info(f"Email successfully sent to {to_email}!")
            return "Email sent successfully"
            
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Authentication failed: {e}"
        logger.error(error_msg)
        logger.error("1. Ensure you're using an App Password (not your regular password)")
        logger.error("2. Verify 2FA is enabled in Google Account settings")
        logger.error("3. Check for suspicious login attempts in your Google account")
        return error_msg
    except smtplib.SMTPException as e:
        error_msg = f"SMTP Error: {e}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logger.error(error_msg)
        return error_msg

if __name__ == "__main__":
    print("mcp_server_6.py starting")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
        print("\nShutting down...") 