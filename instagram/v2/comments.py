from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes, ChallengeRedirection, ChallengeRequired, ChallengeUnknownStep, RecaptchaChallengeForm
import logging
import argparse
import time
import json
import os
from datetime import datetime, timedelta
import signal

logger = logging.getLogger()

# TODO define http proxy link
http_proxy = ''


def parse_args():
    """
    Parses command-line arguments to get user credentials and target Instagram profile
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', type=str, metavar='',
                        help='Username that will be used to access the Instagram account')
    parser.add_argument('-p', '--password', type=str, metavar='',
                        help='Password of the Username that will be used access the Instagram account')
    parser.add_argument('-q', '--query', type=str, metavar='',
                        help='Profile to be searched on Instagram')

    try:
        args = parser.parse_args()
        return args
    except argparse.ArgumentError:
        parser.print_help()
    exit()


def login(cl, username, password):
    """
    Manages login to Instagram, using a proxy to avoid rate limits.
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

    path = f"output/session_{str(username)}.json"
    if os.path.exists(path):
        session = cl.load_settings(path)
        login_via_session = False
        login_via_pw = False
        print("[ig_crawl_console]: Logging into existing session")
        if session:
            try:
                cl.set_settings(session)
                cl.login(username, password)
                try:
                    cl.get_timeline_feed()
                except LoginRequired:
                    logger.info("[ig_crawl_console]: Session is invalid, need to login via username and password")
                    old_session = cl.get_settings()
                    cl.set_settings({})
                    cl.set_uuids(old_session["uuids"])

                    cl.login(username, password)
                login_via_session = True
            except Exception as e:
                logger.info("[ig_crawl_console]: Couldn't login user using session information: %s" % e)

        if not login_via_session:
            try:
                logger.info(
                    "[ig_crawl_console]: Attempting to login via username and password. username: %s" % username)
                if cl.login(username, password):
                    login_via_pw = True
            except Exception as e:
                logger.info("[ig_crawl_console]: Couldn't login user using username and password: %s" % e)

        if not login_via_pw and not login_via_session:
            raise Exception("[ig_crawl_console]: Couldn't login user with either password or session")
    else:
        print("[ig_crawl_console]: Creating new session")
        cl.login(username, password)
        cl.dump_settings(path)


def add_post_info(cl, post):
    """
    Add defined information and comments under the passed post instance
    :param cl: instagrapi client instance
    :param post: individual post to get info for
    """
    post_info = {
        'media_id': post['media_id'],
        'posted_at': post['date'],
        'caption': post['caption'],
        'likes_count': post['num_likes'],
        'comments_count': post['num_comments'],
        'comments': [comment.dict() for comment in cl.media_comments(post['media_id'], 0)],
        'is_sponsored': post['is_sponsored']
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
        # navigate to last media_id
        return data[-1]['media_id']
    except (FileNotFoundError, IndexError, KeyError):
        return None


def save_post_comments(data, filename):
    """
    Each time all the comments from a single post are analyzed, save them to a JSON file
    :param data: information of a single post
    :param filename: name of the file to save the data to
    """
    with open(filename, 'a') as file:
        for item in data:
            json.dump(item, file, indent=4, default=str, ensure_ascii=False)
            file.write(',\n')


def ensure_directories_exist():
    """
    Ensure output directory and subdirs exists
    """
    directories = ['output', 'output/post_comments', 'output/post_info']

    for dir in directories:
        full_path = os.path.join(os.path.dirname(__file__), dir)
        if not os.path.exists(full_path):
            os.makedirs(full_path)


def main():
    ensure_directories_exist()
    args = parse_args()
    input_filename = 'output/post_info/' + str(args.query) + '_post_info.json'
    output_filename = 'output/post_comments/' + str(args.query) + '_post_comments.json'

    post_data = load_post_info(input_filename)
    print("[ig_crawl_console]: Loading json to extract post info")

    last_media_id = get_last_id(output_filename)
    resume = False if last_media_id is None else True

    cl = Client()
    cl.delay_range = [20, 40]
    print("[ig_crawl_console]: Client started")

    # Login to existing session or create new one
    login(cl, args.username, args.password)

    print("[ig_crawl_console]: Extracting comments...")
    for post in post_data:
        # if post['date'] < '2024-01-01 00:00:01 ':
        #   break

        if resume:
            if post['media_id'] != last_media_id:
                continue
            else:
                resume = False
                continue
        try:
            post_info = add_post_info(cl, post)
            save_post_comments([post_info], output_filename)
        except Exception as e:
            if isinstance(e, LoginRequired):
                print("[ig_crawl_wait]: LOGIN REQUIRED, let me sleep and login again")
                time.sleep(30)
                login(cl, args.username, args.password)
                time.sleep(10)
                print("[ig_crawl_wait]: Resume comment extraction...")
                continue
            elif isinstance(e, PleaseWaitFewMinutes):
                current_time = datetime.now()
                time_plus_20_minutes = current_time + timedelta(minutes=20)
                print(f"[ig_crawl_wait]: Please wait a few minutes, until {time_plus_20_minutes.strftime('%H:%M:%S')}")
                time.sleep(1200)
                cl.set_proxy(http_proxy)
                after_ip = cl._send_public_request("https://api.ipify.org/")
                print(f"[proxy]: ...changing proxy to new ip {after_ip}")
                time.sleep(10)
                print("[ig_crawl_wait]: Resume comment extraction...")
                continue
            elif isinstance(e,ChallengeRedirection) or isinstance(e,RecaptchaChallengeForm) or isinstance(e,ChallengeRequired) or isinstance(e,ChallengeUnknownStep):
                current_time = datetime.now()
                time_plus_2_minutes = current_time + timedelta(minutes=2)
                print(f"[ig_crawl_wait]: RESOLVE CHALLENGE, have time until {time_plus_2_minutes.strftime('%H:%M:%S')}")
                time.sleep(120)
                print("[ig_crawl_wait]: Resume comment extraction...")
                continue
            else:
                print(f"[ig_crawl_console]: Error processing post {post['media_id']}:", e)
                break

    print("[ig_crawl_console]: Comments extracted. Logging out.")
    cl.logout()


if __name__ == '__main__':
    main()
