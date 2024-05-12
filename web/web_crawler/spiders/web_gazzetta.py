from scrapy import Spider, Request
from scrapy.selector import Selector
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider

from web_crawler.items import BlogPostItem

import unidecode

class WebCrawlerGazzetta(Spider):
    name = "gazzetta"

    allowed_domains = ["dal15al25.gazzetta.it"]
    start_urls = [
        "https://dal15al25.gazzetta.it/",
    ]

    def parse(self, response):
        # Logic of how to extract the HTML
        article_list = Selector(response).xpath('//*[@class="articles-list"]/article/div/div/p/a')

        next_page = Selector(response).xpath('//*[@class="next-posts"]/a/@href').extract()

        next_page_link = next_page[0] if next_page else None

        for article in article_list:
            # Trigger recursively the parsing of articles
            try:
                article_link = article.xpath('@href').extract()[0]
                yield Request(article_link, callback=self.parse_articles)
            except:
                print(f'[Crawler]: Error crawling an item: {article_link}')
                continue

        # Recursively go to the next page
        if next_page_link:
            yield Request(next_page_link, callback=self.parse)


    def parse_articles(self, response):
        post = BlogPostItem()

        # Format title
        try:
            post['title'] = unidecode.unidecode(response.xpath('//*[@class="article-title"]/h1/text()').extract()[0])

            # Format date
            raw_date = response.xpath('//*[@class="article-datetime"]/text()').extract()[0].strip()
            post['date'] = self.format_date(raw_date)

            #TODO: Instead of putting the date manually made it so that it can set as an input
            if (post['date']) == '30/8/2021':
                print(f'[Crawler]: Crawler reached desired date: {post["date"]}')
                raise CloseSpider()

            # Format content
            post['content'] = unidecode.unidecode(' '.join(response.xpath('//*[@class="article-content"]/p/text()').extract()))

            # Add link
            post['link'] = response.url

            # Add comments
            post['comments'] = []
            comments = response.xpath('//*[@class="commentlist"]/li')
            for comment in comments:
                comment_obj = {
                    'user': comment.xpath('.//*[@class="comment_author"]/text()').extract()[0],
                    'created_at_utc': comment.xpath('.//*[@class="comment_time"]/text()').extract()[0],
                    'text': unidecode.unidecode(" ".join(comment.xpath('.//*[@class="comment_text"]/p/text()').extract())).strip(),
                }
                post['comments'].append(comment_obj)
        except:
            print(f'[Crawler]: Error crawling an item: {response.url}')
        finally:
            yield post

    def map_months(self, month):
        # map the inputs to the function blocks
        months_mapping = {
        'gennaio': '1',
        'febbraio': '2',
        'marzo': '3',
        'aprile': '4',
        'maggio': '5',
        'giugno': '6',
        'luglio': '7',
        'agosto': '8',
        'settembre': '9',
        'ottobre': '10',
        'novembre': '11',
        'dicembre': '12',
        '': ''
        }

        return months_mapping[month]

    def format_date(self, raw_date):
        month = self.map_months(raw_date.split(' ')[1])
        formatted_date = raw_date.split(' ')[0] + "/" + month + "/" + raw_date.split(' ')[2]
        return formatted_date
