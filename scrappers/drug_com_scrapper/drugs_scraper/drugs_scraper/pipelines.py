# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import csv

class DrugsScraperPipeline:    
    def open_spider(self, spider):
        self.file = open('output.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.file, fieldnames=['drug_name', 'sections', 'related_links'])
        self.writer.writeheader()

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        # Flatten the sections dictionary and related_links list for CSV storage
        item['sections'] = "; ".join([f"{k}: {v}" for k, v in item['sections'].items()])
        item['related_links'] = "; ".join([f"{link['label']}: {link['link']}" for link in item['related_links']])
        self.writer.writerow(item)
        return item
