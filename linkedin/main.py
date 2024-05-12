import json
import argparse
from tqdm import tqdm
from argparse import Namespace
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--chromedriver', type=str, metavar='',
                        help='Define path to the chromedriver executable')
    parser.add_argument('-u', '--username', type=str, metavar='',
                        help='Username that will be used to access the LinkedIn account')
    parser.add_argument('-p', '--password', type=str, metavar='',
                        help='Password of the Username that will be used access the LinkedIn account')
    parser.add_argument('-q', '--query', type=str, metavar='', help='Profile to be searched on LinkedIn')
    parser.add_argument('-np', '--numposts', type=int, metavar='', default=3,
                        help='Number of posts to scrape starting from the most recent one')
    parser.add_argument('-cb', '--comments', help='Retrieve or not comments of posts',
                        action='store_true')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    service = Service(args.chromedriver)
    options = Options()
    options.add_argument("--window-size=1920,1080")
    browser = webdriver.Chrome(service=service, options=options)
    browser.implicitly_wait(10)

    if not login(args, browser):
        print("Login failed")
        return
    print("Login successful")

    profile = get_profile(args, browser)
    posts = get_profile_posts(args, browser)
    profile_posts = combine_data(json.loads(profile), json.loads(posts))
    save_to_json(args, profile_posts)

    browser.quit()


def login(args: Namespace, browser: WebDriver) -> bool:
    # get the cookies from the last session
    browser.get('https://www.linkedin.com')
    try:
        with open('last_cookies.json', 'r') as json_file:
            cookies = json.load(json_file)
            for cookie in cookies:
                browser.add_cookie(cookie)
        browser.get('https://www.linkedin.com/feed/')
    except FileNotFoundError:
        browser.get('https://www.linkedin.com/login')
        sleep(2)

        browser.find_element(By.ID, 'username').send_keys(args.username)
        browser.find_element(By.ID, 'password').send_keys(args.password)
        browser.find_element(By.CSS_SELECTOR, '.login__form_action_container button').click()

        if browser.current_url.startswith('https://www.linkedin.com/checkpoint/challenge'):
            remaining_time = 60
            while remaining_time > 0:
                if browser.current_url.startswith('https://www.linkedin.com/feed/'):
                    break
                print(f'\rTime remaining to complete the challenge: {remaining_time} seconds', end='')
                sleep(1)
                remaining_time -= 1
            print('\r', end='')
            if remaining_time == 0:
                return False
        sleep(2)
        cookies = browser.get_cookies()
        data = json.dumps(cookies, indent=4)
        with open('last_cookies.json', 'w') as json_file:
            json_file.write(data)

    if browser.current_url.startswith('https://www.linkedin.com/feed/'):
        return True
    else:
        return False


def get_profile(args: Namespace, browser: WebDriver) -> bytes:
    browser.get("https://www.linkedin.com/in/" + args.query + "/")
    sleep(2)

    page_source = browser.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    name = soup.find('h1',
                     class_='text-heading-xlarge inline t-24 v-align-middle break-words').text.strip()
    subtitle = soup.find('div', class_='text-body-medium break-words').text.strip()
    location = soup.find('span', class_='text-body-small inline t-black--light break-words').text.strip()
    about_section = soup.find('section', class_='artdeco-card pv-profile-card break-words mt2')
    try:
        about = about_section.find('div', class_='display-flex ph5 pv3').div.div.div.span.text.strip()
    except AttributeError:
        about = ""
        pass
    try:
        experience_section = soup.find('div', id='experience').parent
        experiences_html = experience_section.find_all('li', class_='artdeco-list__item')
        experiences = []
        for experience in experiences_html:
            lines_html = experience.find_all('span', class_='visually-hidden')
            experience_lines = []
            for line in lines_html:
                experience_lines.append(line.text.strip())
            experiences.append(experience_lines)
    except AttributeError:
        experiences = []
        pass
    return json.dumps(
        {'name': name, 'subtitle': subtitle, 'location': location, 'about': about, 'experiences': experiences},
        ensure_ascii=False,
        indent=4).encode('utf-8')


def get_profile_posts(args: Namespace, browser: WebDriver) -> bytes:
    browser.get("https://www.linkedin.com/in/" + args.query + "/recent-activity/all/")
    sleep(2)

    soup = BeautifulSoup(browser.page_source, 'html.parser')
    posts = soup.find_all('li', class_='profile-creator-shared-feed-update__container')
    scrolls = 0
    old_num_posts = 0
    old_height = -1
    print("Looking for posts:")
    pbar = tqdm(total=(args.numposts + 20) // 20 * 20)
    while len(posts) < args.numposts + 20:
        scroll_height = f"window.scrollTo(0, {1080 * scrolls});"
        browser.execute_script(scroll_height)
        sleep(1)
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        posts = soup.find_all('li', class_='profile-creator-shared-feed-update__container')
        num_posts = len(posts) - 19
        if 0 <= num_posts != old_num_posts:
            pbar.update(num_posts - old_num_posts)
            old_num_posts = num_posts
        height = browser.execute_script("return document.documentElement.scrollTop")
        if old_height == height:
            pbar.update(len(posts))
            args.numposts = len(posts)
            break
        old_height = height
        scrolls += 1
    pbar.close()

    browser.execute_script("window.scrollTo(0, 0);")
    sleep(1)

    if args.comments:
        print("Looking for comments: ")
        comments_buttons = browser.find_elements(By.CLASS_NAME, 'comment-button')
        comments_buttons = comments_buttons[:args.numposts] if len(
            comments_buttons) > args.numposts else comments_buttons
        for i in tqdm(range(len(comments_buttons))):
            try:
                browser.execute_script("arguments[0].click();", comments_buttons[i])
                sleep(1)
                height = browser.execute_script("return document.documentElement.scrollTop")
                for j in range(5):
                    browser.execute_script(f"window.scrollTo(0, {height + 1080 * j});")
                    sleep(1)
            except Exception:
                pass

    print("Retrieving posts (and comments):")
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    posts = soup.find_all('li', class_='profile-creator-shared-feed-update__container')
    posts = posts[:args.numposts] if len(posts) > args.numposts else posts
    json_posts = []
    for i in tqdm(range(len(posts))):
        try:
            post_text = posts[i].find('span', class_='break-words').span.text.strip()
            json_posts.append({'post': post_text, 'comments': []})
            if args.comments:
                comments = posts[i].find_all('article', 'comments-comment-item comments-comments-list__comment-item')
                for comment in comments:
                    try:
                        comment_author = comment.find('span',
                                                      class_='comments-post-meta__name-text').span.span.text.strip()
                        comment_text = comment.find('div', class_='update-components-text').span.text.strip()
                        json_posts[-1]['comments'].append({'author': comment_author, 'comment': comment_text})
                    except AttributeError:
                        pass
        except AttributeError:
            pass
    return json.dumps(json_posts, ensure_ascii=False, indent=4).encode('utf-8')


def combine_data(profile_data, posts_data) -> bytes:
    profile_data['posts'] = posts_data
    return json.dumps(profile_data, ensure_ascii=False, indent=4).encode('utf-8')


def save_to_json(args: Namespace, data):
    filename = "linkedin_" + args.query + ".json"
    with open(filename, 'w') as json_file:
        json_file.write(data.decode('utf-8'))
    print("Data has been written to " + filename)


if __name__ == '__main__':
    main()
