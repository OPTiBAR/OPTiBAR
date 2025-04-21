import re

def password_validator(passwd):
    val = True
    message = None
    if len(passwd) < 6 or len(passwd) > 20:
        message = 'length should be at least 6 and not greater than 20'
        val = False

    if not any(char.isdigit() for char in passwd):
        message = 'Password should have at least one numeral'
        val = False

    if not any(char.isalpha() for char in passwd):
        message = 'Password should have at least one letter'
        val = False
          
    if not any(char.islower() for char in passwd):
        print('sina lower')
        message = 'Password should have at least one lowercase letter'
        val = False
    
    return {
        'is_valid': val,
        'message': message,
    }

def phone_validator(phone):
    matched = re.match(r'(0|\+98)?([ ]|-|[()]){0,2}9[1|2|3|4]([ ]|-|[()]){0,2}(?:[0-9]([ ]|-|[()]){0,2}){8}', phone)
    return {
        'is_valid':bool(matched),
        'message': 'The Phone number is not valid',
    }
        