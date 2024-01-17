import time
from flask import Flask, jsonify, Response
import json
from instagrapi import Client
from instagrapi.types import User
import re  

app = Flask(__name__)

INSTAGRAM_USERNAME = 'starbuzz286'
INSTAGRAM_PASSWORD = 'Starbuzz123@'

proxy = "socks5://yoqytafd-6:2dng483b96qx@p.webshare.io:80"
cl = Client(proxy=proxy)

try:
    cl.load_settings('session-loop286.json')
    cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
except Exception as e:
    print(f"Instagram login failed: {e}")


def extract_user_data(user: User):
    return {
        'username': user.username,
        'full_name': user.full_name,
        'media_count': user.media_count,
        'follower_count': user.follower_count,
        'following_count': user.following_count,
        'biography': user.biography,
    }



def is_valid_phone_number(number):
    cleaned_number = number.replace(" ", "")
    
    if cleaned_number.startswith('91'):
        return len(cleaned_number) == 12  
    elif cleaned_number.startswith('+91'):
        return len(cleaned_number) == 13  
    else:
        return len(cleaned_number) == 10


def extract_phone_number(bio):
    phone_pattern_additional = re.compile(r'\b\d+\s?\d+\s?\d+\b')
    phone_numbers_additional = re.findall(phone_pattern_additional, bio)

    phone_pattern_with_spaces = re.compile(r'\b\d+\s?\d+\b')
    phone_numbers_with_spaces = re.findall(phone_pattern_with_spaces, bio)
    
    phone_pattern_without_spaces = re.compile(r'\b\d+\b')
    phone_numbers_without_spaces = re.findall(phone_pattern_without_spaces, bio)

    phone_pattern = re.compile(r'\b(?:\+91)?\d{10}\b|\b\+91\d{12}\b')
    phone_numbers_spa = re.findall(phone_pattern, bio)
    
    valid_phone_numbers_additional = [number for number in phone_numbers_additional if is_valid_phone_number(number)]
    valid_phone_numbers_with_spaces = [number for number in phone_numbers_with_spaces if is_valid_phone_number(number)]
    valid_phone_numbers_without_spaces = [number for number in phone_numbers_without_spaces if is_valid_phone_number(number)]
    valid_phone_numbers_spa = [number for number in phone_numbers_spa if is_valid_phone_number(number)]
    
    all_valid_phone_numbers = (
        valid_phone_numbers_additional +
        valid_phone_numbers_with_spaces +
        valid_phone_numbers_without_spaces +
        valid_phone_numbers_spa
    )

    valid_phone_numbers = list(set(all_valid_phone_numbers))
    
    print(valid_phone_numbers, "valid_phone_numbers")
    verified_phone_numbers = [number for number in valid_phone_numbers if is_valid_phone_number(number)]
    print("verified_phone_numbers",verified_phone_numbers)
    return verified_phone_numbers


def extract_email(bio):
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    email_matches = re.findall(email_pattern, bio)
    return email_matches

@app.route('/profile/<accountname>')
def get_profile(accountname):
    max_retries = 3
    retry_delay = 5

    for retry_number in range(1, max_retries + 1):
        try:
            profile_info = cl.user_info_by_username(accountname)
            if profile_info is not None:
                data = extract_user_data(profile_info)
                
                phone_numbers = extract_phone_number(data['biography'])
                email = extract_email(data['biography'])

                phone_number_list = list(set(filter(None, [profile_info.public_phone_number, profile_info.contact_phone_number]+ phone_numbers)))
                data['phone_number'] = phone_number_list if phone_number_list else None
                combined_emails = list(set(filter(None, [profile_info.public_email] + email)))
                data['email'] = combined_emails if combined_emails else None


                response = {
                    'success': True,
                    'message': 'Data retrieved successfully',
                    'data': data
                }
                json_data = json.dumps(response, ensure_ascii=False)
                return Response(json_data, content_type='application/json; charset=utf-8')
            else:
                response = {
                    'success': False,
                    'message': 'Profile not found',
                    'data': None
                }
                return jsonify(response)
        except Exception as e:
            if "429" in str(e):
                print(f"Rate limit exceeded. Retrying in {retry_delay} seconds (Retry {retry_number}/{max_retries}).")
                time.sleep(retry_delay)
            else:
                response = {
                    'success': False,
                    'message': f"An error occurred while fetching profile: {e}",
                    'data': None
                }
                return jsonify(response)

    response = {
        'success': False,
        'message': 'Max retries reached. Unable to fetch profile.',
        'data': None
    }
    return jsonify(response)

if __name__ == '__main__':
    try:
        app.run(debug=False)
    except Exception as e:
        print(f"An error occurred: {e}")