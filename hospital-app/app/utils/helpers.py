"""
OpenCareOS - Utility Functions
Apache License 2.0
"""

import re
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Any
from uuid import UUID


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def generate_mrn() -> str:
    """Generate a Medical Record Number."""
    # Format: MRN-YYYY-XXXXXX
    year = datetime.utcnow().year
    random_part = secrets.randbelow(1000000)
    return f"MRN-{year}-{random_part:06d}"


def generate_confirmation_code(prefix: str = "APT") -> str:
    """Generate a confirmation code."""
    random_part = secrets.randbelow(1000000)
    return f"{prefix}-{random_part:06d}".upper()


def hash_file_content(content: bytes) -> str:
    """Calculate SHA256 hash of file content."""
    sha256 = hashlib.sha256()
    sha256.update(content)
    return sha256.hexdigest()


def calculate_bmi(height_cm: float, weight_kg: float) -> Optional[float]:
    """Calculate BMI from height and weight."""
    if height_cm <= 0 or weight_kg <= 0:
        return None
    height_m = height_cm / 100
    bmi = weight_kg / (height_m * height_m)
    return round(bmi, 1)


def calculate_age(date_of_birth: datetime) -> int:
    """Calculate age from date of birth."""
    today = datetime.utcnow().date()
    dob = date_of_birth.date() if isinstance(date_of_birth, datetime) else date_of_birth
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def is_minor(date_of_birth: datetime) -> bool:
    """Check if person is a minor (< 18 years)."""
    return calculate_age(date_of_birth) < 18


def format_phone_number(phone: str) -> str:
    """Format phone number for display."""
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return phone


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove path traversal attempts
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    # Keep only safe characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255 - len(ext) - 1] + ('.' + ext if ext else '')
    return filename


def get_file_extension(filename: str) -> str:
    """Get file extension in lowercase."""
    return filename.split('.')[-1].lower() if '.' in filename else ''


def is_allowed_file_type(mime_type: str, allowed_types: List[str]) -> bool:
    """Check if MIME type is in allowed list."""
    return mime_type in allowed_types


def format_file_size(bytes_size: int) -> str:
    """Format file size in human readable format."""
    if bytes_size == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(bytes_size)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.1f} {units[i]}"


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data showing only last N characters."""
    if len(data) <= visible_chars:
        return '*' * len(data)
    return '*' * (len(data) - visible_chars) + data[-visible_chars:]


def parse_duration(duration_str: str) -> Optional[timedelta]:
    """Parse duration string (e.g., '30m', '2h', '1d') to timedelta."""
    match = re.match(r'^(\d+)([mhd])$', duration_str.lower())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    if unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    return None


def format_duration(td: timedelta) -> str:
    """Format timedelta to human readable string."""
    total_seconds = int(td.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds}s"
    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    minutes = minutes % 60
    if hours < 24:
        if minutes == 0:
            return f"{hours}h"
        return f"{hours}h {minutes}m"
    days = hours // 24
    hours = hours % 24
    if hours == 0:
        return f"{days}d"
    return f"{days}d {hours}h"


def paginate_list(items: List[Any], page: int, size: int) -> dict:
    """Paginate a list of items."""
    total = len(items)
    start = (page - 1) * size
    end = start + size
    pages = (total + size - 1) // size
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


def deep_merge(dict1: dict, dict2: dict) -> dict:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_async(func, max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry an async function with exponential backoff."""
    import asyncio

    async def wrapper(*args, **kwargs):
        last_exception = None
        current_delay = delay
        for attempt in range(max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        raise last_exception
    return wrapper