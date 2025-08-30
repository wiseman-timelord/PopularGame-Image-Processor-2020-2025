import os

def get_console_width():
    """
    Gets the current width of the console window.
    Returns a default value if the size cannot be determined.
    """
    try:
        # This is the most reliable cross-platform method
        return os.get_terminal_size().columns
    except OSError:
        # Fallback for environments without a real terminal (e.g., some IDEs)
        return 80

def print_separator(char='='):
    """
    Prints a separator line that spans the full width of the console.
    """
    width = get_console_width()
    print(char * width)

def print_header(title, char='='):
    """
    Prints a formatted header with a title, wrapped in separator lines.
    """
    print_separator(char)
    print(title)
    print_separator(char)

def clear_screen():
    """Clears the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')
