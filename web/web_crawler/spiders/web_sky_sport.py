from scrapy import Spider, Request
from scrapy.selector import Selector
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from web_crawler.items import BlogPostItem

import unidecode

class WebCrawlerSkySport(Spider):
    name = "sky_sport"

    allowed_domains = ["sport.sky.it"]
    start_urls = [
        "https://sport.sky.it/argomenti/",
    ]

    def parse(self, response):
        # Logic of how to extract the HTML
        news_list = Selector(response).xpath('//*[@class="c-card  c-card--CA25-m c-card--CA25-t c-card--CA25-d c-card--no-abstract-m c-card--media  c-card--base"]')

        # Link of next page
        next_page = Selector(response).xpath('//*[@class="c-pagination__arrow-next"]/@href').extract()
        next_page_link = next_page[0] if next_page else None

        for news_item in news_list:
            # Trigger recursively the parsing of posts
            news_link = news_item.xpath('@href').extract()[0]
            yield Request(news_link, callback=self.parse_posts)

        # Recursively go to the next page
        if next_page_link:
            yield Request(next_page_link, callback=self.parse)

    def parse_posts(self, response):
        post = BlogPostItem()

        # Format title
        post['title'] = unidecode.unidecode(response.xpath('//*[@class="c-hero__title c-hero__title-content j-hero__title"]/text()').extract()[0])

        # Format date
        raw_date = response.xpath('//*[@class="c-hero__date"]/@datetime').extract()[0]
        post['date'] = raw_date

        #TODO: Instead of putting the date manually made it so that it can set as an input
        if '2021-09-01' in (post['date']):
            print(f'[Crawler]: Crawler reached desired date: {post["date"]}')
            raise CloseSpider()

        # Format text
        raw_text = response.xpath('//*[@class="c-article-section j-article-section l-spacing-m"]/p')
        inner_text = self.format_innertext(raw_text)
        # Format accents and special characters
        formatted_text = unidecode.unidecode(inner_text[0] if inner_text else "")
        post['content'] = formatted_text

        # Add Link
        post['link'] = response.url

        yield post

    def format_innertext(self, elements, delimiter=" "):
        return list(delimiter.join(el.strip() for el in element.css('*::text').getall()) for element in elements)
