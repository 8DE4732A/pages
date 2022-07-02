# -*- coding: UTF-8 -*-
from bs4 import BeautifulSoup, Tag
from datetime import datetime
import urllib.request
import sys
import json
import re
import sqlite3

from bson import encode

def parse_index() -> list:
    req = urllib.request.Request(url='https://www.cnbeta.com/', 
    headers={'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"})
    result = []
    with urllib.request.urlopen(req) as f, open(sys.path[0] + '/debug.html', 'w+', encoding='utf-8') as w:
        data = f.read()
        w.write(data.decode('utf-8'))
        soap = BeautifulSoup(data.decode('utf-8'), "html.parser")
        items = soap.find('div', class_='items-area').find_all('div', class_='item', limit=999)
        print(len(items))
        for item in items:
            if item.dl and 'cnbeta' in item.dl.dt.a['href']:
                url = item.dl.dt.a['href']
                if 'http' not in url:
                    url = 'https:' + url
                result.append({
                    "url": url,
                    "title": item.dl.dt.a.string,
                    "desc": item.dl.dd.p.string,
                })
    return result

def parse_article(url: str) -> str:
    print(url)
    req = urllib.request.Request(url=url, 
    headers={'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"})
    with urllib.request.urlopen(req) as f:
        # w.write(f.read().decode('utf-8'))
        soap = BeautifulSoup(f.read(), "html.parser")
        # print(soap)
        # print(soap.find('header', class_='title'))
        return {
            "images": find_images((soap.find('div', class_='cnbeta-article-body').find('div', class_='article-summary'), soap.find('div', class_='cnbeta-article-body').find('div', class_='article-content'))),
            "summary": get_content(soap.find('div', class_='cnbeta-article-body').find('div', class_='article-summary')),
            "content": get_content(soap.find('div', class_='cnbeta-article-body').find('div', class_='article-content')),
            "title": soap.find('header', class_='title').h1.string,
        }

def find_images(tags: tuple):
    result = []
    for tag in tags:
        for one in tag.find_all('img'):
            result.append(one['src'])
    return result

def get_content(tag: Tag) -> str:
    remove_ad(tag)
    remove_class(tag)
    remove_style(tag)
    remove_id(tag)
    return str(tag)

def remove_ad(tag: Tag):
    remove = []
    remove.append(tag.find('div', class_='article-global'))
    remove.append(tag.find('div', class_='article-topic'))
    for one in remove:
        if one:
            one.decompose()
    # for one in tag.find_all(target='_blank'):
    #     if one:
    #         one.decompose()

def remove_class(tag: Tag):
    del tag['class']
    for one in tag.find_all(lambda tag: tag.has_attr('class')):
        del one['class']

def remove_style(tag: Tag):
    del tag['style']
    for one in tag.find_all(lambda tag: tag.has_attr('style')):
        del one['style']

def remove_id(tag: Tag):
    del tag['id']
    for one in tag.find_all(lambda tag: tag.has_attr('id')):
        del one['id']



if __name__ == '__main__':
    index = parse_index()[::-1]
    print(len(index))
    conn = sqlite3.connect(sys.path[0] + '/cnbeta.db', isolation_level=None)
    cur = conn.cursor()
    for one in index:
        c = cur.execute("select count(1) from article where url = ?", (one['url'],)).fetchone()[0]
        if c == 0 :
            article = parse_article(one['url'])
            data = (
                one['title'],
                one['desc'],
                one['url'],
                article['summary'],
                article['content'],
                int(datetime.now().timestamp())
            )
            cur.execute("insert into article (title, desc, url, summary, content, gmt_created) values (?,?,?,?,?,?)", data)
            # print(article['images'])
            for url in article['images']:
                req = urllib.request.Request(url=url, 
                headers={'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"})
                with urllib.request.urlopen(req) as f:
                    d = f.read()
                    cur.execute("insert into images (url, image) values (?,?)", (url, d))
    with open(sys.path[0] + '/result.json', 'w+', encoding='utf-8') as f:
        f.write(json.dumps(index, ensure_ascii=False,indent=4, separators=(',', ':')))