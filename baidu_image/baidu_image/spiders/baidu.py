# -*- coding: utf-8 -*-
import scrapy
from baidu_image.items import BaiduImageItem

class BaiduSpider(scrapy.Spider):
    name = 'baidu'
    allowed_domains = ['image.baidu.com']
    #start_urls = ['http://image.baidu.com/']
    #https://image.baidu.com/search/flip?tn=baiduimage&word=%E5%A3%81%E7%BA%B8&pn=20
    #start_urls = ['https://image.baidu.com/search/flip?tn=baiduimage&word=%E5%A3%81%E7%BA%B8&pn=20']

    def start_requests(self):
        your_word = input("请输入关键词: ")
        yield scrapy.Request(url='https://image.baidu.com/search/flip?tn=baiduimage&word=' + your_word)

    def parse(self, response):
        item = BaiduImageItem()
        item['titles'] = response.xpath('//script/text()').re(r'"fromPageTitle":"(.*?)(?=",\s*"bdSourceName")')
        item['image_urls'] = response.xpath('//script/text()').re(r'"objURL":"(\S*?)"')
        #print(len(item['titles']), len(item['image_urls']))
        yield item

        for next_url in response.xpath('//div[@id="page"]/a[@class="n"]').css('a::attr(href)').extract(): 
            if next_url:
                url = response.urljoin('http://image.baidu.com/' + next_url)
                #print(url)
                yield scrapy.Request(url, self.parse)
