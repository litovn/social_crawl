This package operates without the need for Chromedriver, unlike other crawlers. Before utilizing this package, ensure that you set up a virtual environment and install all dependencies listed in requirements.txt.

# Sections
- [V1](#V1)
- [V2](#V2)

---
## V1
This package was initially designed as a comprehensive tool for extracting detailed information from posts on public profiles. However, through practical application, it has proven to be most effective for analyzing the first few dozen recent posts rather than over extended periods. While the code may still function, please note that it is currently unmaintained to focus on [V2](#V2).

### CLI - examples
An example of command is (in the following a detailed explanation is provided):
```
python3 main.py --username '<your_username>' --password '<your_password>' --query '<profile_to_analyze>' ...etc         #invoked to get a json with informations related to the defined number of posts
python3 comments.py --username '<your_username>' --password '<your_password>' --query '<profile_to_analyze>'            #invoked to get comments for the posts extracted in the json run by main.py
```

### Files Usage
- [main.py](v1/main.py), provides a comprehensive tool for interacting with Instagram, tailored to gather various types of information of a post based on user-defined criteria.
  - [posts.py](v1/ig_postget/posts.py), toolkit for automated interactions with Instagram invoked by [main.py](v1/main.py).
- [comments.py](v1/ig_postget/comments.py), tailored for users needing to programmatically extract detailed comment data from Instagram.


### Command Line
You can use this package from command line, `postget` will:
1. Login a new session and create a **session.json** or a previously created one by selecting the **session.json**
   1. *The **session.json** is needed to simulate a saved login from the same device. In real life, you login to Instagram on a device once and then you can use it for a long time without logging in again;*
   2. *To mitigate the risks of your account being suspended, if multiple requests are sent in a short timeframe the package will throw an exception;*
   3. *If you are willing to take risks, you can manually delete the created session.json file and the package will run the same as the first time you booted it.*
2. Search for the query according to the operating mode
3. Save found information in a **.json** file that can be used in a MongoDB environment according to the operating mode
4. Close the driver

### Main parameters in the initialization
Parameter | type                                                                    | Description
--- |-------------------------------------------------------------------------| ---
`username` | (`str`):                                                                |Username that will be used to access the Instagram account
`password` | (`str`):                                                                |Password of the Username that will be used access the Instagram account
`query` | (`str`):                                                                |Profile to be searched on Instagram
`reels` | (`bool` if imported, just type `--reels` if called from command line):  |Call with this if you want get list of reels as the only media
`tag` | (`bool` if imported, just type `--tag` if called from command line):    |Call with this if you want get list of only the posts the user was tagged in
`hashtag` | (`str`):                                                                |Hashtag to be searched on Instagram. With a list of related posts under the hashtag
`recent_hash` | (`int`):                                                                |Return the selected amount of most recent posts by hashtag. If set to `-1` (default value) this parameter will not be considered.
`top_hash` | (`int`):                                                                |Return the selected amount of top posts by hashtag. If set to `-1` (default value) this parameter will not be considered.
`num_posts` | (`int`):                                                                |Number of posts to scrape starting from the most recent one. Set to `3` (default value).
`bio` | (`bool` if imported, just type `--bio` if called from command line):    |Call with this if you also want get the bio of the user you are searching for
`followers` | (`int`):                                                                |Call with this if you also want get a list of the amount of users who followers the user. If set to `-1` (default value) this parameter will not be considered.
`following` | (`int`):                                                                |Call with this if you also want get a list of the amount of users who the user follows. If set to `-1` (default value) this parameter will not be considered.
`story` | (`int`):                                                                |Call with this if you also want get a list of the amount of stories published by the user. If set to `-1` (default value) this parameter will not be considered.


### Comments parameters in the initialization
Parameter | type                                                                    | Description
--- |-------------------------------------------------------------------------| ---
`username` | (`str`):                                                                |Username that will be used to access the Instagram account
`password` | (`str`):                                                                |Password of the Username that will be used access the Instagram account
`query` | (`str`):                                                                |Profile to be searched on Instagram
`comments` | (`int`):                                                                |Number of comments to scrape from each post. Set to `0` (default value) means all the comments of the post will be saved.


---

## V2
This package was designed as a comprehensive tool for extracting only essential information from posts on public profiles in a large timeframe. The package works by:
1. Run [main.py](v2/main.py) to save a list of essential info of posts in a json, following the below pattern:

Keyword | Description
--- | ---
`media_id`  |ID of the post
`date`      |Date when the post was posted on the platform. String in the following format `YYYY-MM-DD HH:MM:SS`
`caption`       |Caption written under the post
`is_sponsored`     |Check if the post is flagged as sponsored
`num_likes`       |Number of likes under the post
`num_comments`       |Number of comments under the post

2. Run [comments.py](v2/comments.py) if also interested in adding a 1 `comment: [{...}]` section, with information regarding all the comments under a post.

### CLI - examples
An example of command is (in the following a detailed explanation is provided):
```
python3 main.py --username '<your_username>' --password '<your_password>' --query '<profile_to_analyze>'         #invoked to get a json with informations related to the defined number of posts
python3 comments.py --username '<your_username>' --password '<your_password>' --query '<profile_to_analyze>'     #invoked to get comments for the posts extracted in the json run by main.py
```
### Parameters in the initialization
Parameter | type                                                                    | Description
--- |-------------------------------------------------------------------------| ---
`username` | (`str`):                                                                |Username that will be used to access the Instagram account
`password` | (`str`):                                                                |Password of the Username that will be used access the Instagram account
`query` | (`str`):                                                                |Profile to be searched on Instagram
