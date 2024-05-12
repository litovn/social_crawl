import instaloader
from datetime import datetime
import argparse
import json
import os


def parse_args():
    """
    Define a function to parse command-line arguments
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
    # Defines the output JSON file name based on the query
    output_file_name = 'output/post_info/' + str(args.query) + '_post_info.json'
    # Session file to store login session
    session_file = f"output/session_{str(args.username)}.json"

    # Configuring the Instaloader instance
    L = instaloader.Instaloader()
    L.download_pictures = False  # Disable downloading pictures
    L.download_videos = False  # Disable downloading videos
    L.download_video_thumbnails = False  # Disable downloading thumbnails
    L.save_metadata = False  # Disable saving metadata
    L.download_geotags = False  # Disable downloading geotags
    L.download_comments = False  # Disable downloading comments

    # Session handling to avoid re-login on every run
    if os.path.exists(session_file):
        L.load_session_from_file(args.username, session_file)
    else:
        L.login(args.username, args.password)
        L.save_session_to_file(session_file)

    # Fetching posts from the specified profile
    profile = instaloader.Profile.from_username(L.context, args.query)
    posts_data = []
    for post in profile.get_posts():
        # if post.caption:
           # caption_lower = post.caption.lower()
            # if any(keyword in caption_lower for keyword in ["pallavolo", "verovolley"]):
                post_data = {
                    'media_id': post.mediaid,
                    'date': post.date_utc,
                    'caption': post.caption,
                    'is_sponsored': post.is_sponsored,
                    'num_likes': post.likes,
                    'num_comments': post.comments
                }

                # TODO define date where to stop, if needed
                # Stop fetching posts before a specific date
                # if post.date_utc < datetime.strptime('2021-09-01 00:00:01', '%Y-%m-%d %H:%M:%S'):
                #     break
                posts_data.append(post_data)

    # Saving the fetched data to a JSON file
    json_data = json.dumps(posts_data, indent=4, default=str, ensure_ascii=False)
    with open(output_file_name, 'w') as f:
        f.write(json_data)

    print(f'Saved {len(posts_data)} media IDs to media_ids.json')


if __name__ == '__main__':
    main()
