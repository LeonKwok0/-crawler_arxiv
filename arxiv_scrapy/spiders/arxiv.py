# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.cmdline import execute
from scrapy.http import Request
from arxiv_scrapy.items import ArxivScrapyItem
import logging
logger = logging.getLogger(__name__)

class ArxivSpider(scrapy.Spider):
    name = 'arxiv'
    page_size = 100
    allowed_domains = ['arxiv.org']
    base_url = "https://arxiv.org"
    start_urls = ['http://arxiv.org/']

    def start_requests(self):
        """
        构造url
        """
        config = {"cs.OS": ["20"+("0"+str(item)if item < 10 else str(item)) for item in range(1, 13)],
                  "cs.GL": ["20"+("0"+str(item)if item < 10 else str(item)) for item in range(1, 13)]
                  }
        for cat, dates in config.items():
            for date in dates:
                url = f"{self.base_url}/list/{cat}/{date}?show={self.page_size}"
                yield Request(url, callback=self.process_list_page,
                              meta={"url": url, "scrap_next_page":True}
                            )
                              

    def process_list_page(self, response):
        """
        处理列表页
        from url:https://arxiv.org/list/cs/2101?show=100
        """
        # process this page
        paper_urls = response.xpath('//span[@class="list-identifier"]/a[1]/@href').extract()
        for paper_url in paper_urls:
            url = self.base_url + paper_url
            yield Request(url, callback=self.parse_paper_page)
    
        # 翻页
        scrap_next_page = response.meta["scrap_next_page"]
        if not scrap_next_page:
            return
        url_prefix = response.meta["url"]
        total_str = response.xpath('//*[@id="dlpage"]/small[1]/text()').extract_first()
        if not total_str:
            logging.warning(f"Page {response.url} is empty")
            return
        num_str = re.search("[0-9]+",total_str).group(0)
        num = int(num_str)
        for skip in range(self.page_size,num,self.page_size):
            url = f"{url_prefix}&skip={skip}"
            yield Request(url, callback=self.process_list_page,
                              meta={"scrap_next_page": False}
                        )

    def parse_paper_page(self, response):
        """
        处理paper 页
        """
        print (response.url)
        title = response.xpath('//div[@id="abs"]/h1/text()').extract()
        if title:
            title = title[0]
        abstract = response.xpath('//div[@id="abs"]/blockquote/text()').extract()
        if abstract:
            abstract = abstract[1]
        subjects_main = response.xpath('//span[@class="primary-subject"]/text()').extract()
        if subjects_main:
            subjects_main = subjects_main[0]
        subjects_other =response.xpath('//td[@class="tablecell subjects"]/text()').extract()
        if len(subjects_other) == 2:
            subjects_other = subjects_other[1]
        
        item = ArxivScrapyItem()
        item['title'] = title
        item['abstract'] = abstract
        item['subjects_main'] = subjects_main
        item['subjects_other'] = subjects_other
        return item
        


    
        


if __name__ == "__main__":
    execute(['scrapy','crawl','arxiv'])
    
