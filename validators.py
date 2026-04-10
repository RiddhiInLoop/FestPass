import re

def is_valid_email(email: str) -> bool:
    """Validates an email address and ensures it ends with @despu.edu.in."""
    if not email:
        return False # Email is now required for OTP
    pattern = r"^[a-zA-Z0-9_.+-]+@despu\.edu\.in$"
    return re.match(pattern, email) is not None

def is_valid_roll_no(roll_no: str) -> bool:
    """Validates that a roll number is provided and alphanumeric."""
    if not roll_no:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", roll_no))

def is_valid_seat(seat: str) -> bool:
    """Validates the seat format: alphanumeric and 1 to 10 characters long."""
    if not seat:
        return False
    # To support string like 'A1' or '100' or 'VIP-1' we check length. 
    # Alphanumeric with spaces or hyphens might be needed, defining a simple length and basic characters check.
    if len(seat) < 1 or len(seat) > 10:
        return False
    return bool(re.match(r"^[a-zA-Z0-9\s-]+$", seat))

def is_valid_name(name: str) -> bool:
    """Validates that a name is provided and within a reasonable length limit."""
    if not name:
        return False
    return 1 <= len(name) <= 100
