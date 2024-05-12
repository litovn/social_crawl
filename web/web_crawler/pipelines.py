# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json


class WebCrawlerPipeline:
    def open_spider(self, spider):
        print('[Crawler]: Opening crawler...')
        self.file = open(f'{spider.name}_output.json', 'w')
        # Your scraped items will be saved in the file 'scraped_items.json'.
        # You can change the filename to whatever you want.
        self.file.write("[")

    def close_spider(self, spider):
        print('[Crawler]: Closing crawler...')
        self.file.write("]")
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(
            dict(item),
            indent = 4,
            separators = (',', ': ')
        ) + ",\n"
        self.file.write(line)
        return item
