from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes, ClientError
import logging
from datetime import datetime
import time
import json
import os

logger = logging.getLogger()

# TODO define http proxy link
http_proxy = ''

class InstaPosts:
    def __init__(self, username: str, password: str, query: str, hashtag: str, reels: bool = False, tag: bool = False,
                 recent_hash: int = -1, top_hash: int = -1, num_posts: int = 3, bio: bool = False, followers: int = -1,
                 following: int = -1, story: int = -1):
        """
        Constructor with numerous parameters for various search and filter options
        """

        print("[ig_postget]: You or your program started InstaPostget")
        # Parameters initialization
        self.username = username
        self.password = password
        self.query = query
        self.output_file_name = 'output/post_info/' + query + '_post_info.json'
        self.reels = reels
        self.tag = tag
        self.hashtag = hashtag
        self.recent_hash = recent_hash
        self.top_hash = top_hash
        self.num_posts = num_posts
        self.bio = bio
        self.followers = followers
        self.following = following
        self.story = story

        # Initialization of dictionary
        self.results = {}
        self.medias = []
        self.hashtag_info = None

        # Initialization of instagrapi
        print("[ig_postget]: Initializing client")
        self.cl = Client()
        self.login_user()
        print("[ig_postget]: Login successful")
        self.cl.delay_range = [30, 60]
        self.user_id = None

    def login_user(self):
        """
        Method to handle login and setup a proxy for the Instagrapi client
        """
        print("[proxy]: Setting up proxy...")
        # Handling of proxy setup and IP change confirmation
        before_ip = self.cl._send_public_request("https://api.ipify.org/")
        print(f"[proxy]: ...previous ip {before_ip}")

        # TODO insert proxy http link
        self.cl.set_proxy(http_proxy)

        after_ip = self.cl._send_public_request("https://api.ipify.org/")
        print(f"[proxy]: ...current ip {after_ip}")

        # Create a session for logged in user
        path = f"session_{self.username}.json"
        if os.path.exists(path):
            session = self.cl.load_settings(path)
            login_via_session = False
            login_via_pw = False
            print("[ig_postget]: Logging into existing session")
            if session:
                try:
                    self.cl.set_settings(session)
                    self.cl.login(self.username, self.password)
                    try:
                        self.cl.get_timeline_feed()
                    except LoginRequired:
                        logger.info("[ig_postget]: Session is invalid, need to login via username and password")
                        old_session = self.cl.get_settings()
                        self.cl.set_settings({})
                        self.cl.set_uuids(old_session["uuids"])

                        self.cl.login(self.username, self.password)
                    login_via_session = True
                except Exception as e:
                    logger.info("[ig_postget]: Couldn't login user using session information: %s" % e)

            if not login_via_session:
                try:
                    logger.info(
                        "[ig_postget]: Attempting to login via username and password. username: %s" % self.username)
                    if self.cl.login(self.username, self.password):
                        login_via_pw = True
                except Exception as e:
                    logger.info("[ig_postget]: Couldn't login user using username and password: %s" % e)

            if not login_via_pw and not login_via_session:
                raise Exception("[ig_postget]: Couldn't login user with either password or session")
        else:
            print("[ig_postget]: Creating new session")
            self.cl.login(self.username, self.password)
            self.cl.dump_settings(path)

    def get_media(self, amount: int):
        """
        Crawl the defined number of posts of the given profile starting from the most recent one
        :param amount: number of media/posts to analyze
        """
        self.user_id = self.cl.user_id_from_username(self.query)
        if self.reels:
            print("[ig_postget]: Retrieving reel media type")
            self.medias = self.cl.user_clips(self.user_id, amount)
        elif self.tag:
            print("[ig_postget]: Retrieving tag media type")
            self.medias = self.cl.usertag_medias_gql(self.user_id, amount)
        else:
            print("[ig_postget]: Retrieving all media type")
            try:
                self.medias = self.cl.user_medias_v1(self.user_id, amount)
                return self.medias
            except ClientError as e:
                self.medias = self.cl.user_medias_gql(self.user_id, amount)
                return self.medias

    def get_hashtag(self):
        """
        Crawl the defined number of posts of the given hashtag starting from the most recent one
        """
        print("[ig_postget]: Researching hashtags")
        self.hashtag_info = self.cl.hashtag_info(self.hashtag)
        if self.recent_hash != -1:
            self.medias = self.cl.hashtag_medias_recent(self.hashtag, self.recent_hash)
        if self.top_hash != -1:
            self.medias = self.cl.hashtag_medias_top(self.hashtag, self.top_hash)

    def fetch_post_data(self, medias):
        """
        Iterative fetching of precise data for each single found post
        :param medias: list of media objects
        """
        print("[ig_postget]: Retrieving post data")
        self.results["media"] = []
        self.results["hashtag"] = []
        if self.hashtag:
            self.results["hashtag"].append(self.hashtag_info.dict())

        for media in medias:
            try:
                media_dict = media.dict()
                self.results["media"].append(media_dict)
            # Error handling and retry logic for request failures or rate limits
            except Exception as e:
                if e == LoginRequired or e == 'login required':
                    time.sleep(15)
                    self.login_user()
                    time.sleep(10)
                    pass
                elif e == PleaseWaitFewMinutes or e == 'Please wait a few minutes before you try again':
                    time.sleep(15)
                    self.cl.set_proxy(http_proxy)
                    after_ip = self.cl._send_public_request("https://api.ipify.org/")
                    print(f"[proxy]: ...changing proxy to new ip {after_ip}")
                    time.sleep(120)
                    pass
                else:
                    print(f"[ig_postget]: Error processing post {media.id}:", e)
                    break
        # Saving of fetched data upon successful retrieval or error
        self.save()
        print("[ig_postget]: All media processed. Data saved to .json")

    def get_bio(self):
        """
        Fetch and save bio data if requested
        """
        if self.bio:
            print("[ig_postget]: Retrieving bio")
            self.results["bio"] = []
            user_bio = self.cl.user_info(self.user_id)
            self.results["bio"].append(user_bio.dict())

    def get_followers(self):
        """
        Fetch and save follower list if requested
        """
        if self.followers != -1:
            print("[ig_postget]: Retrieving list of followers")
            self.results["followers"] = self.cl.user_followers(self.user_id, True, self.followers)

    def get_following(self):
        """
        Fetch and save following list if requested
        """
        if self.following != -1:
            print("[ig_postget]: Retrieving list of following")
            self.results["following"] = self.cl.user_following(self.user_id, True, self.following)

    def get_story(self):
        """
        Fetch and save stories if requested
        """
        if self.story != -1:
            print("[ig_postget]: Retrieving stories of user")
            self.results["story"] = []
            stories = self.cl.user_stories(self.user_id, self.story)
            for story in stories:
                story_dict = story.dict()
                self.results["story"].append(story_dict)

    def save(self):
        """
        Save all collected data to a JSON file specified by 'output_file_name'
        """
        print("[ig_postget]: Saving parsed data in .json")
        json_data = json.dumps(self.results, indent=4, default=str, ensure_ascii=False)
        with open(self.output_file_name, 'w') as json_file:
            json_file.write(json_data)

    def clear_media(self):
        """
        Reset data storage variables to clear fetched media
        """
        self.results = {}
        self.medias = []

    def logout(self):
        """
        Logout from the Instagrapi client
        """
        print("[ig_postget]: logging out")
        self.cl.logout()
