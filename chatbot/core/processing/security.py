import bcrypt
import re
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password (str): The plain text password to hash
        
    Returns:
        str: The hashed password
    """
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password (str): The plain text password to verify
        hashed_password (str): The hashed password to check against
        
    Returns:
        bool: True if the password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.
    
    Args:
        text (str): The text to sanitize
        
    Returns:
        str: The sanitized text
    """
    if not text:
        return ""
    
    try:
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove potentially dangerous characters
        text = re.sub(r'[<>{}[\]\\]', '', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Trim whitespace
        text = text.strip()
        
        return text
    except Exception as e:
        logger.error(f"Error sanitizing input: {e}")
        return ""

def validate_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a person's name.
    
    Args:
        name (str): The name to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        if not name:
            return False, "Name is required"
        
        if len(name) < 2:
            return False, "Name must be at least 2 characters long"
        
        if len(name) > 50:
            return False, "Name must not exceed 50 characters"
        
        if not re.match(r'^[a-zA-Z\s\-\.\']+$', name):
            return False, "Name can only contain letters, spaces, hyphens, periods, and apostrophes"
        
        if re.search(r'\s{2,}', name):
            return False, "Name cannot contain multiple consecutive spaces"
        
        return True, None
    except Exception as e:
        logger.error(f"Error validating name: {e}")
        return False, "Error validating name"

def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a phone number format.
    
    Args:
        phone (str): The phone number to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        if not phone:
            return False, "Phone number is required"
        
        # Remove any spaces, dashes, or parentheses
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Check if it's exactly 10 digits
        if not phone.isdigit() or len(phone) != 10:
            return False, "Phone number must be exactly 10 digits"
        
        # Check for all zeros
        if phone == '0' * 10:
            return False, "Invalid phone number"
        
        # Check for sequential numbers
        if re.search(r'(\d)\1{9}', phone):
            return False, "Invalid phone number pattern"
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'^1234567890$',  # Sequential
            r'^9876543210$',  # Reverse sequential
            r'^1111111111$',  # All same digits
            r'^0000000000$',  # All zeros
            r'^9999999999$',  # All nines
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, phone):
                return False, "Invalid phone number pattern"
        
        return True, None
    except Exception as e:
        logger.error(f"Error validating phone: {e}")
        return False, "Error validating phone number"

def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an email address format.
    
    Args:
        email (str): The email address to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        if not email:
            return False, "Email is required"
        
        # Basic email format validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        # Check for common disposable email domains
        disposable_domains = [
            'tempmail.com', 'throwawaymail.com', 'mailinator.com',
            'guerrillamail.com', '10minutemail.com', 'yopmail.com'
        ]
        domain = email.split('@')[1].lower()
        if domain in disposable_domains:
            return False, "Disposable email addresses are not allowed"
        
        # Check for maximum length
        if len(email) > 254:  # RFC 5321
            return False, "Email address is too long"
        
        # Check for consecutive dots
        if '..' in email:
            return False, "Invalid email format"
        
        # Check for special characters in local part
        local_part = email.split('@')[0]
        if re.search(r'[<>()[\]\\,;:\s"]', local_part):
            return False, "Invalid characters in email address"
        
        return True, None
    except Exception as e:
        logger.error(f"Error validating email: {e}")
        return False, "Error validating email"

def validate_account_number(account: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a bank account number format.
    
    Args:
        account (str): The account number to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        if not account:
            return False, "Account number is required"
        
        # Check if it's exactly 10-12 digits
        if not account.isdigit() or not (10 <= len(account) <= 12):
            return False, "Account number must be 10-12 digits"
        
        # Check for all zeros
        if account == '0' * len(account):
            return False, "Invalid account number"
        
        # Check for sequential numbers
        if re.search(r'(\d)\1{9}', account):
            return False, "Invalid account number pattern"
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'^1234567890$',  # Sequential
            r'^9876543210$',  # Reverse sequential
            r'^1111111111$',  # All same digits
            r'^0000000000$',  # All zeros
            r'^9999999999$',  # All nines
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, account):
                return False, "Invalid account number pattern"
        
        return True, None
    except Exception as e:
        logger.error(f"Error validating account number: {e}")
        return False, "Error validating account number"

def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength.
    
    Args:
        password (str): The password to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        if not password:
            return False, "Password is required"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 128:
            return False, "Password must not exceed 128 characters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[@$!%*#?&]', password):
            return False, "Password must contain at least one special character (@$!%*#?&)"
        
        # Check for common passwords
        common_passwords = [
            'password', '123456', 'qwerty', 'admin', 'welcome',
            'letmein', 'monkey', 'dragon', 'baseball', 'football'
        ]
        if password.lower() in common_passwords:
            return False, "This is a common password. Please choose a stronger one"
        
        # Check for sequential characters
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            return False, "Password contains sequential characters"
        
        # Check for repeated characters
        if re.search(r'(.)\1{2,}', password):
            return False, "Password contains too many repeated characters"
        
        return True, None
    except Exception as e:
        logger.error(f"Error validating password strength: {e}")
        return False, "Error validating password"