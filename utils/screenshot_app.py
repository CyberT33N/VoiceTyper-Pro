#!/usr/bin/env python3
import subprocess
import time
import os
from datetime import datetime
import sys
from PIL import ImageGrab
import tkinter as tk

def capture_using_import(output_path):
    """
    Capture active window using the 'import' command from ImageMagick.
    Returns: True if successful, False otherwise
    """
    try:
        # First activate the window (optional, may already be active)
        subprocess.run("xdotool windowactivate $(xdotool getactivewindow)", shell=True)
        time.sleep(0.5)  # Give it a moment to activate
        
        # Use the import command to capture the active window
        # -window root captures the entire screen, but we'll use 'import -window "$(xdotool getactivewindow)"'
        # to capture only the active window
        command = f'import -window "$(xdotool getactivewindow)" "{output_path}"'
        result = subprocess.run(command, shell=True)
        
        if result.returncode == 0 and os.path.exists(output_path):
            print(f"Successfully captured window using import command to: {output_path}")
            return True
    except Exception as e:
        print(f"Error using import command: {e}")
    
    return False

def capture_active_window_with_gtk():
    """
    Capture the active window using GTK on Linux
    Returns: (x, y, width, height) or None if failed
    """
    try:
        # Try using GDK to get active window info
        from gi.repository import Gdk
        
        # Get default screen and active window
        display = Gdk.Display.get_default()
        screen = display.get_default_screen()
        active_window = screen.get_active_window()
        
        if active_window:
            # Get geometry
            x, y, width, height = active_window.get_geometry()
            # Get position
            root_x, root_y = active_window.get_root_origin()
            return (root_x, root_y, width, height)
    except Exception as e:
        print(f"GTK window capture failed: {e}")
    
    return None

def start_app_and_take_screenshot(delay=5):
    """
    Start the main.py app and take a screenshot after a specified delay.
    
    Args:
        delay (int): Number of seconds to wait before taking screenshot
    """
    print(f"Starting main.py application...")
    
    # Get the absolute path to the main directory
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_script = os.path.join(main_dir, "main.py")
    
    # Start the main.py in a separate process
    process = subprocess.Popen([sys.executable, main_script], 
                              stderr=subprocess.PIPE)
    
    # Wait for the specified delay to let the app initialize
    print(f"Waiting {delay} seconds for the application to initialize...")
    
    # Check if process terminated early (indicating an error)
    for _ in range(delay):
        time.sleep(1)
        if process.poll() is not None:
            # Process has terminated
            _, stderr = process.communicate()
            print(f"Error: Application failed to start properly:")
            print(stderr.decode())
            return
    
    # Take screenshot
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_dir = os.path.join(main_dir, "screenshots")
        
        # Create screenshots directory if it doesn't exist
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            
        screenshot_path = os.path.join(screenshot_dir, f"app_screenshot_{timestamp}.png")
        
        # Find the app window
        if sys.platform == "linux" or sys.platform == "linux2":
            # Try first using the 'import' command from ImageMagick (best for window captures on Linux)
            screenshot_taken = False
            
            # Check if import command is available
            if subprocess.run("which import", shell=True, stdout=subprocess.PIPE).returncode == 0:
                print("Trying to capture using import command...")
                screenshot_taken = capture_using_import(screenshot_path)
            
            # If import command failed or not available, try xdotool method
            if not screenshot_taken:
                window_geometry = None
                
                # Try using xdotool
                try:
                    # List of possible window titles/patterns to search for
                    window_titles = [
                        "VoiceTyper Pro",
                        "Voice Typer",
                        "VoiceTyper",
                        "customtkinter",
                        ".*Voice.*",  # Regex pattern to match any window with Voice in the title
                        ".*Typer.*"   # Regex pattern to match any window with Typer in the title
                    ]
                    
                    window_id = None
                    # Try each window title until we find a match
                    for title in window_titles:
                        try:
                            result = subprocess.check_output(f"xdotool search --name '{title}'", shell=True).decode().strip()
                            if result:
                                window_id = result.split('\n')[0]  # Take the first window if multiple found
                                print(f"Found window with title containing '{title}': {window_id}")
                                break
                        except subprocess.CalledProcessError:
                            continue
                    
                    if not window_id:
                        # Last resort: try to find any new window that appeared in the last 'delay' seconds
                        print("Couldn't find specific window, trying to activate it...")
                        subprocess.run("xdotool windowactivate $(xdotool getactivewindow)", shell=True)
                        time.sleep(1)  # Give it a moment to activate
                        window_id = subprocess.check_output("xdotool getactivewindow", shell=True).decode().strip()
                    
                    if window_id:
                        # Get window geometry
                        try:
                            window_info = subprocess.check_output(f"xdotool getwindowgeometry {window_id}", shell=True).decode()
                            
                            # Parse position and size
                            position_line = [line for line in window_info.split('\n') if "Position" in line][0]
                            size_line = [line for line in window_info.split('\n') if "Geometry" in line][0]
                            
                            x, y = map(int, position_line.split(':')[1].strip().split(','))
                            width, height = map(int, size_line.split(':')[1].strip().split('x'))
                            
                            # Store window geometry
                            window_geometry = (x, y, width, height)
                        except Exception as e:
                            print(f"Error getting window geometry with xdotool: {e}")
                except Exception as e:
                    print(f"Error finding window with xdotool: {e}")
                
                # If xdotool failed, try GTK method
                if window_geometry is None:
                    print("Trying GTK method for window capture...")
                    try:
                        window_geometry = capture_active_window_with_gtk()
                    except Exception as e:
                        print(f"GTK window capture failed: {e}")
                
                # If we have window geometry, take screenshot of that specific region
                if window_geometry:
                    x, y, width, height = window_geometry
                    
                    # Add a small padding to ensure we get the entire window including borders
                    x = max(0, x - 5)
                    y = max(0, y - 5)
                    width += 10
                    height += 10
                    
                    # Capture the specific region
                    screenshot = ImageGrab.grab(bbox=(x, y, x+width, y+height))
                    screenshot.save(screenshot_path)
                    print(f"Window screenshot saved to: {screenshot_path}")
                    screenshot_taken = True
                
                # If all methods failed, take full screenshot
                if not screenshot_taken:
                    print("Window detection failed, taking full screenshot instead")
                    screenshot = ImageGrab.grab()
                    screenshot.save(screenshot_path)
                    print(f"Full screenshot saved to: {screenshot_path}")
                
        elif sys.platform == "win32":
            # For Windows
            import pygetwindow as gw
            try:
                # Try different window titles
                window_titles = ['VoiceTyper Pro', 'Voice Typer', 'VoiceTyper']
                window = None
                
                for title in window_titles:
                    windows = gw.getWindowsWithTitle(title)
                    if windows:
                        window = windows[0]
                        print(f"Found window with title: {title}")
                        break
                
                if window:
                    # Add small padding to ensure we get the entire window
                    left = max(0, window.left - 5)
                    top = max(0, window.top - 5)
                    right = window.right + 5
                    bottom = window.bottom + 5
                    
                    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
                    screenshot.save(screenshot_path)
                    print(f"Window screenshot saved to: {screenshot_path}")
                else:
                    print("Window not found, taking full screenshot instead")
                    screenshot = ImageGrab.grab()
                    screenshot.save(screenshot_path)
                    print(f"Full screenshot saved to: {screenshot_path}")
            except Exception as e:
                print(f"Error finding window: {e}")
                screenshot = ImageGrab.grab()
                screenshot.save(screenshot_path)
                print(f"Full screenshot saved to: {screenshot_path}")
        elif sys.platform == "darwin":
            # For macOS
            try:
                # Use applescript to get window position and size
                script = """
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                    tell process frontApp
                        set appWindow to first window
                        set {x, y} to position of appWindow
                        set {width, height} to size of appWindow
                        return x & "," & y & "," & width & "," & height
                    end tell
                end tell
                """
                result = subprocess.check_output(["osascript", "-e", script]).decode().strip()
                x, y, width, height = map(int, result.split(','))
                
                # Add small padding
                x = max(0, x - 5)
                y = max(0, y - 5)
                width += 10
                height += 10
                
                screenshot = ImageGrab.grab(bbox=(x, y, x+width, y+height))
                screenshot.save(screenshot_path)
                print(f"Window screenshot saved to: {screenshot_path}")
            except Exception as e:
                print(f"Error finding window: {e}")
                screenshot = ImageGrab.grab()
                screenshot.save(screenshot_path)
                print(f"Full screenshot saved to: {screenshot_path}")
        else:
            # Fallback to full screen for other platforms
            screenshot = ImageGrab.grab()
            screenshot.save(screenshot_path)
            print(f"Full screenshot saved to: {screenshot_path}")
        
        # Ask user if they want to close the app
        response = input("Do you want to close the application? (y/n): ")
        if response.lower() == 'y':
            process.terminate()
            print("Application terminated.")
        else:
            print("Application left running. You can close it manually.")
            print("The script will now exit, but the app will continue running.")
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        process.terminate()

if __name__ == "__main__":
    # You can modify the delay (in seconds) if needed
    start_app_and_take_screenshot(5) 