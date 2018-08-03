# -*- coding: utf-8 -*-
"""百度图片爬取

windows10 
python -v 3.4.4
以下代码仅供学习交流之用
"""

import requests
import os
import re
from bs4 import BeautifulSoup
from multiprocessing import Pool

#获取网页源代码
def get_webpage(keyword):
    url = 'http://image.baidu.com/search/index?'
    search_params = {
        'tn':'baiduimage',
        'word':keyword
    }

    try:
        r = requests.get(url, params=search_params, timeout=9)
    except requests.exceptions.RequestException:
        print("网络异常！")
    else:
        r.encoding = 'utf-8'
        return r.text

#获取相关搜索的关键词
def get_contact_word(webpage):
    s = BeautifulSoup(webpage, 'lxml').find_all('a', class_='pull-rs')
    for item in s:
        yield item.string

#获取最初显示的图片
def get_begin_image(webpage):
    s = BeautifulSoup(webpage, 'lxml').find_all('script', type='text/javascript')
    url_pattern = re.compile(r'"objURL":"(\S*?)"')  #链接
    urls = [url for url in url_pattern.findall(str(s))]
    title_pattern = re.compile(r'"fromPageTitle":"(.*?)(?=",\s*"bdSourceName")')  #标题
    titles = [title for title in title_pattern.findall(str(s))]
    image_dict = dict(zip(titles, urls))
    return image_dict

"""参数意思
(注:并未使用)
'rn':'30',    每页图片链接数
'gsm':'3c',   十六进制计数参数，和pn相等
'1531450518385':''  时间戳，int(time.time()*1000)

objURL(big size)链接是加密的，暂时选择thumbURL(low size)代替
"""
# 获取剩余Ajax图片
def get_ajax_image(keyword, pn):
    url = 'https://image.baidu.com/search/acjson'
    search_params = {
        'tn':'resultjson_com',
        'ipn':'rj',
        'word':keyword,
        'pn':pn
        }

    try:
        r = requests.get(url, params=search_params, timeout=9)
    except requests.exceptions.RequestException:
        print("网络异常！")
    else:
        r.encoding = 'utf-8'
        """json处理方式
        
        #第一种直接使用requests自带的json()：
        image_dict = {item.get('fromPageTitleEnc'):item.get('thumbURL') for item in r.json().get('data') if len(item) != 0}
        #第二种使用json模块
        s = re.sub(r'\\', '', r.text)
        try:
            for item in json.loads(s, strict=False).get('data'):
                print(len(item))
        except Exception as e:
            traceback.print_exc(e)
            print(s)
        共同缺点: 由于返回的个别数据并不标准会导致json无法解析
        """
        #改用正则匹配
        title_pattern = re.compile(r'"fromPageTitleEnc":"(.*?)(?=",\s*"bdSourceName")')  #标题
        titles = [title for title in title_pattern.findall(r.text)]
        url_pattern = re.compile(r'"thumbURL":"(\S*?)"')  #链接
        urls = [url for url in url_pattern.findall(r.text)]
        image_dict = dict(zip(titles, urls))
        return image_dict
        
#去除标题中的非法字符
def remove_illegal_sign(title):      
    #windows下文件命名禁止使用的字符 |<>/\:*?"
    new_title = re.sub(r'[|<>/\\:*?"]', '', title)
    return new_title

#下载图片
def download_image(title, url, file_path):
    if url is not None:
        try:
            image_file = requests.get(url, stream=True, timeout=9)
        except requests.exceptions.RequestException:
            print("网络异常！")
        else:
            if image_file.status_code is not requests.codes.ok:
                print('{}'.format(url) + "  链接为空！")
            else:
                name = remove_illegal_sign(title)
                if name is '':
                    name = file_path.split('\\')[-1]
                image_file_path = '{}\\{}.jpg'.format(file_path, name)
                #避免同名图片被覆盖
                count = 1
                while (os.path.isfile(image_file_path)):
                    count += 1
                    image_file_path = '{}\\{}{}.jpg'.format(file_path, name, count)
                print("正在下载:" + '{}.jpg'.format(name))
                with open(image_file_path, 'wb') as f:
                    for chunk in image_file.iter_content(chunk_size=1024*16):
                        f.write(chunk)

def ctrl_c(a, b):
    print(a, b)
    os.exit(0)
                
if __name__ == '__main__':
    your_word = input("请输入关键词: ")
    download_word = [your_word]  #download_word会随着程序运行不断增大
    while (len(download_word) != 0):
        webpage = get_webpage(download_word[0])
        file_path = '{}\\{}\\{}'.format(os.getcwd(), "百度图片", download_word[0])  #程序文件所在目录建立图片文件夹
        if os.path.exists(file_path):
            pass  #目标关键词已经下载过了 
        else:
            os.makedirs(file_path)
            print('*'*50 + '\n正在下载:{}\n文件目录:{}\n'.format(download_word[0], file_path) + '*'*50)
            p = Pool(10)
            for title, url in get_begin_image(webpage).items():
                p.apply_async(download_image, args=(title, url, file_path))
            p.close()
            p.join()
            pn = 30
            while (len(get_ajax_image(download_word[0], pn)) != 0):
                p = Pool(10)
                for title, url in get_ajax_image(download_word[0], pn).items():
                    p.apply_async(download_image, args=(title, url, file_path))
                p.close()
                p.join()
                pn += 30
            
        download_word.remove(download_word[0])
        for i in get_contact_word(webpage):
            download_word.append(i)

#ctrl+c 的问题
#使用python自带IDLE,子进程不会打印出信息,使用命令行运行程序可以输出信息
# 图片会下载重复？？