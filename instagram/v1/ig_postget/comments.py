from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes
from datetime import datetime, timedelta
import logging
import argparse
import time
import json
import os

# Global variables for file names based on a predefined profile name
# TODO define profile name
profile_name = ''
input_filename = 'output/post_info/' + profile_name + '_post_info.json'
output_filename = 'output/post_comments/' + profile_name + '_post_comments.json'

# TODO insert proxy http link
http_proxy = ''

logger = logging.getLogger()


def parse_args():
    """
    Function to parse command-line arguments for user credentials and comment scraping preferences
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', type=str, metavar='',
                        help='Username that will be used to access the Instagram account')
    parser.add_argument('-p', '--password', type=str, metavar='',
                        help='Password of the Username that will be used access the Instagram account')
    parser.add_argument('-c', '--comments', type=int, metavar='', default=0,
                        help='Number of comments to scrape from each post. 0 means all the comments')
    try:
        args = parser.parse_args()
        return args
    except argparse.ArgumentError:
        parser.print_help()
    exit()


def login(cl, username, password):
    """
    Function to log in to Instagram, using a proxy for security and to prevent rate limiting
    :param cl: instagrapi client instance
    :param username: given args.username to login into Instagram account
    :param password: given args.password to login into Instagram account
    """
    print("[proxy]: Setting up proxy...")
    # Use proxy server to mitigate limit rate
    before_ip = cl._send_public_request("https://api.ipify.org/")
    print(f"[proxy]: ...previous ip {before_ip}")
    cl.set_proxy(http_proxy)
    after_ip = cl._send_public_request("https://api.ipify.org/")
    print(f"[proxy]: ...current ip {after_ip}")

    # Create a session for logged in user
    path = f"session_{username}.json"
    if os.path.exists(path):
        session = cl.load_settings(path)
        login_via_session = False
        login_via_pw = False
        print("[ig_postget]: Logging into existing session")
        if session:
            try:
                cl.set_settings(session)
                cl.login(username, password)
                try:
                    cl.get_timeline_feed()
                except LoginRequired:
                    logger.info("[ig_postget]: Session is invalid, need to login via username and password")
                    old_session = cl.get_settings()
                    cl.set_settings({})
                    cl.set_uuids(old_session["uuids"])

                    cl.login(username, password)
                login_via_session = True
            except Exception as e:
                logger.info("[ig_postget]: Couldn't login user using session information: %s" % e)

        if not login_via_session:
            try:
                logger.info(
                    "[ig_postget]: Attempting to login via username and password. username: %s" % username)
                if cl.login(username, password):
                    login_via_pw = True
            except Exception as e:
                logger.info("[ig_postget]: Couldn't login user using username and password: %s" % e)

        if not login_via_pw and not login_via_session:
            raise Exception("[ig_postget]: Couldn't login user with either password or session")
    else:
        print("[ig_postget]: Creating new session")
        cl.login(username, password)
        cl.dump_settings(path)


def add_post_info(cl, post):
    """
    Process data of a single instagram post
    :param cl: instagrapi client instance
    :param post: single post instance
    """
    post_info = {
        'media_id': post['id'],
        'posted_at': post['taken_at'],
        'thumbnail_url': post['thumbnail_url'],
        'caption_text': post['caption_text'],
        'comments_count': post['comment_count'],
        'likes_count': post['like_count'],
        'comments': [comment.dict() for comment in cl.media_comments(post['media_id'], 0)]
    }

    return post_info


def load_post_info(filename):
    """
    Function to load post data from a JSON file, in case it was previously stopped
    :param filename: name of the file to resume
    """
    with open(filename, 'r') as file:
        return json.load(file)


def get_last_id(filename):
    """
    Function to get the ID of the last processed post, to resume operations
    :param filename: name of the file to get last id from (if it was previously stopped)
    """
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
        return data[-1]['media_id']
    # Error handling for file or data access issues
    except (FileNotFoundError, IndexError, KeyError):
        return None


def save_post_comments(data, filename):
    """
    Function to save comments to a JSON file
    :param data: completely processed data of the single post
    :param filename: file name to save content to
    """
    with open(filename, 'a') as file:
        for item in data:
            json.dump(item, file, indent=4, default=str, ensure_ascii=False)
            file.write(',\n')


def main():
    args = parse_args()
    post_data = load_post_info(input_filename)
    print("[ig_postget]: Loading json to extract post info")

    last_media_id = get_last_id(output_filename)
    resume = False if last_media_id is None else True

    cl = Client()
    cl.delay_range = [30, 60]
    print("[ig_postget]: Client started")

    # Login to existing session or create new one
    login(cl, args.username, args.password)

    # Process comments from posts, handling pagination and errors
    print("[ig_postget]: Extracting comments...")
    for post in post_data['media']:
        if resume:
            if post['id'] != last_media_id:
                continue
            else:
                resume = False
        try:
            # Fetch and save comments
            post_info = add_post_info(cl, post)
            save_post_comments([post_info], output_filename)
        # Error handling and retry logic for request failures or rate limits
        except Exception as e:
            if isinstance(e, LoginRequired):
                time.sleep(30)
                login(cl, args.username, args.password)
                time.sleep(10)
                pass
            elif isinstance(e, PleaseWaitFewMinutes):
                current_time = datetime.now()
                time_plus_20_minutes = current_time + timedelta(minutes=20)
                print(f"Please wait a few minutes, until {time_plus_20_minutes.strftime('%H:%M:%S')}")
                time.sleep(1200)
                cl.set_proxy(http_proxy)
                after_ip = cl._send_public_request("https://api.ipify.org/")
                print(f"[proxy]: ...changing proxy to new ip {after_ip}")
                time.sleep(10)
                pass
            else:
                print(f"[ig_postget]: Error processing post {post['id']}:", e)
                break

    print("[ig_postget]: Comments extracted. Logging out.")
    cl.logout()


if __name__ == '__main__':
    main()
