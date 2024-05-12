# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BlogPostItem(scrapy.Item):
    # define the fields for item :
    title = scrapy.Field()
    date = scrapy.Field()
    link = scrapy.Field()
    content = scrapy.Field()
    taken_at = scrapy.Field()
    comment_count = scrapy.Field()
    comments = scrapy.Field()
    pass
