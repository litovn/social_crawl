class WrongDateString(Exception):
    def __init__(self, format_received, format_requested):
        self.format_received = format_received
        self.format_requested = format_requested
        message = f'[postget]: The {format_received} date is in an incorrect format. Please use {format_requested}'
        super().__init__(message)