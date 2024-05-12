import argparse
import sys
from ig_postget.posts import InstaPosts


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
    parser.add_argument('-r', '--reels', action='store_true',
                        help='Call with this if you want get list of reels as the only media')
    parser.add_argument('-t', '--tag', action='store_true',
                        help='Call with this if you want get list of only the posts the user was tagged in')
    parser.add_argument('-hash', '--hashtag', type=str, metavar='',
                        help='Hashtag to be searched on Instagram. With a list of related posts under the hashtag')
    parser.add_argument('-rh', '--recent_hash', type=int, metavar='', default=-1,
                        help='Return the selected amount of most recent posts by hashtag')
    parser.add_argument('-th', '--top_hash', type=int, metavar='', default=-1,
                        help='Return the selected amount of top posts by hashtag')
    parser.add_argument('-np', '--num_posts', type=int, metavar='', default=3,
                        help='Number of posts to scrape starting from the most recent one')
    parser.add_argument('--bio', action='store_true',
                        help='Call with this if you also want get the bio of the user you are searching for')
    parser.add_argument('--followers', type=int, metavar='', default=-1,
                        help='Call with this if you also want get a list of the amount of users who followers the user')
    parser.add_argument('--following', type=int, metavar='', default=-1,
                        help='Call with this if you also want get a list of the amount of users who the user follows')
    parser.add_argument('--story', type=int, metavar='', default=-1,
                        help='Call with this if you also want get a list of the amount of stories published by the user')
    try:
        args = parser.parse_args()
        return args
    except argparse.ArgumentError:
        parser.print_help()
    exit()


def main():
    """
    Main function to execute the program
    """
    args = parse_args()

    # Handle invalid combinations of arguments with error messages:
    #  - You can either search for all media, only reels or only tagged posts
    if args.reels and args.tag:
        print("Error: Please specify either --reels or --tag, but not both.")
        sys.exit(1)

    #  - You can either search for a profile or a hashtag, not both
    if args.query and args.hashtag:
        print("Error: Please specify either --query or --hashtag, but not both.")
        sys.exit(1)
    elif not args.query and not args.hashtag:
        print("Error: Please specify either --query or --hashtag.")
        sys.exit(1)

    #  - No option to search tagged posts of a hashtag exists
    if args.hashtag and args.tag:
        print("Error: No --tag option exists for --hashtag.")
        sys.exit(1)

    #  - You can either search for the most recent or the top posts of a hashtag, not both
    if args.hashtag and args.recent_hash != -1 and args.top_hash != -1:
        print("Error: Please specify either --recent_hash or --top_hash, but not both.")
        sys.exit(1)

    # Initialize the Instagram interaction object
    ig_getter = InstaPosts(args.username, args.password, args.query, args.hashtag, args.reels, args.tag, args.recent_hash,
                           args.top_hash, args.num_posts, args.bio, args.followers, args.following, args.story)

    # Retrieve and process media based on the specified criteria
    medias = []
    if args.query:
        print("... Retrieving media from query")
        medias = ig_getter.get_media(args.num_posts)
    elif args.hashtag:
        print("... Retrieving media from hashtag")
        ig_getter.get_hashtag()

    # Fetch additional data if requested
    ig_getter.fetch_post_data(medias)

    if args.bio:
        ig_getter.get_bio()
    if args.followers:
        ig_getter.get_followers()
    if args.following:
        ig_getter.get_following()
    if args.story:
        ig_getter.get_story()

    # Clear media and logout after operations
    print("... Clearing Media")
    ig_getter.clear_media()
    ig_getter.logout()


if __name__ == '__main__':
    main()
