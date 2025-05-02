# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
from pywinauto.application import Application
import win32gui
import win32con
import time
from win32api import GetSystemMetrics
import pywinauto.keyboard
import win32api
import pyautogui
import pydirectinput

# instantiate an MCP server client
mcp = FastMCP("Calculator")

# DEFINE TOOLS

#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from getpass import getpass  # For secure password input

@mcp.tool()
def send_email(
    subject="Computed Result using MCP",
    body="This is a default email body."
):
    """
    Sends an email using SMTP.
    
    Args:
        subject (str): Email subject. Default: "Automated Email from Python".
        body (str): Plain text email body. Ignored if html_body is provided.
    """
    # Secure credential handling
    # if from_email is None:
    #     from_email = input("Enter your email (e.g., your_name@gmail.com): ")
    # password = getpass("Enter your email password/App Password: ")

    # Configuration
    to_email = "anandsharespace@gmail.com"
    from_email = "anandsharespace@gmail.com"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    password = ""

    # Create message
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    body = "The computed result = " + body

    msg.attach(MIMEText(body, "plain"))

    # Enhanced error handling
    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.set_debuglevel(1)  # Enable SMTP protocol logging
            print(">>> Connecting to server...")
            server.starttls()
            print(">>> TLS started. Attempting login...")
            server.login(from_email, password)
            print(">>> Login successful. Sending email...")
            server.send_message(msg)
            print(f">>> Email successfully sent to {to_email}!")
            return True
            
    except smtplib.SMTPAuthenticationError as e:
        print(f"Authentication failed: {e}")
        print("1. Ensure you're using an App Password (not your regular password)")
        print("2. Verify 2FA is enabled in Google Account settings")
        print("3. Check for suspicious login attempts in your Google account")
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return False
        

@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Get primary monitor width to adjust coordinates
        primary_width = GetSystemMetrics(0)
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.2)
        
        # pyautogui.click(x=100, y=100)

        # Click on the Rectangle tool using the correct coordinates for secondary screen
        paint_window.click_input(coords=(540, 85))
        time.sleep(1.0)
        
        # Select rectangle tool (Alt+H, R in English versions)
        # pywinauto.keyboard.send_keys('%hr')
        # time.sleep(0.5)

        # Get the canvas area
        # canvas = paint_window.child_window(class_name='MSPaintView')
        
        # # Draw rectangle - coordinates should already be relative to the Paint window
        # # No need to add primary_width since we're clicking within the Paint window
        # canvas.press_mouse_input(coords=(x1, y1), button="left")
        # time.sleep(0.5) 
        # canvas.move_mouse_input(coords=(x2, y2))
        # time.sleep(0.5) 
        # canvas.release_mouse_input(coords=(x2, y2), button="left")

        pydirectinput.moveTo(x1, y1)
        pydirectinput.mouseDown()
        pydirectinput.moveTo(x2, y2, duration=0.5)
        pydirectinput.mouseUp()

        # Use win32api for reliable mouse control
        # def smooth_drag(start_x, start_y, end_x, end_y):
        #     win32api.SetCursorPos((start_x, start_y))
        #     win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        #     time.sleep(0.1)
            
        #     # Smooth movement
        #     steps = 10
        #     for i in range(1, steps+1):
        #         interim_x = int(start_x + (end_x - start_x) * i/steps)
        #         interim_y = int(start_y + (end_y - start_y) * i/steps)
        #         win32api.SetCursorPos((interim_x, interim_y))
        #         time.sleep(0.02)
            
        #     win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

        # # Perform the drawing
        # smooth_drag(x1, y1, x2, y2)
        # time.sleep(0.3)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Add text in Paint"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.5)
        
        # Click on the Rectangle tool
        # paint_window.click_input(coords=(528, 92))
        # time.sleep(0.5)
        
        # # Select rectangle tool (Alt+H, R in English versions)
        # pywinauto.keyboard.send_keys('%hr')
        # time.sleep(0.5)

        # Step 1: Select the Text Tool using keyboard shortcuts
        pydirectinput.keyDown('t')  # Press 'T' for Text Tool
        time.sleep(0.2)
        pydirectinput.keyUp('t')    # Release 'T'
        time.sleep(0.5)

        pydirectinput.keyDown('x')  # Press 'X' to toggle background
        time.sleep(0.2)
        pydirectinput.keyUp('x')    # Release 'X'
        time.sleep(0.5)
        
        # Click where to start typing
        # canvas.click_input(coords=(810, 533))
        # time.sleep(0.5)

        pydirectinput.moveTo(800, 425)
        pydirectinput.click()  # Left-click to place text cursor
        time.sleep(0.5)
        
        # Type the text passed from client
        # paint_window.type_keys(text)
        pydirectinput.write(text, interval=0.1)
        time.sleep(0.5)
        
        # Click to exit text mode
        # canvas.click_input(coords=(1050, 800))
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text:'{text}' added successfully"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint maximized on primary monitor"""
    global paint_app
    try:
        paint_app = Application().start('mspaint.exe')
        time.sleep(0.2)
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Get primary monitor width
        primary_width = GetSystemMetrics(0)
        
        # First move to secondary monitor without specifying size
        win32gui.SetWindowPos(
            paint_window.handle,
            win32con.HWND_TOP,
            1, 0,  # Position it on primary monitor
            0, 0,  # Let Windows handle the size
            win32con.SWP_NOSIZE  # Don't change the size
        )
        
        # Now maximize the window
        win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
        time.sleep(0.2)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text="Paint opened successfully on primary monitor and maximized"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error opening Paint: {str(e)}"
                )
            ]
        }
# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
