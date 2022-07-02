import json
import sys
import sqlite3
from sqlite3 import Cursor
from pathlib import Path
from bs4 import BeautifulSoup, Tag

from numpy import True_

def gen_artical(all : bool = False):
    conn = sqlite3.connect(sys.path[0] + '/cnbeta.db')
    cur = conn.cursor()
    if all:
        data = cur.execute('select id, title, summary, content from article').fetchall()
    else:
        data = cur.execute('select id, title, summary, content from article where done is null').fetchall()
    for one in data:
        page = f'''
        <html lang="en">
            <head>
                <meta charset="utf-8">
                <title>{one[1]}</title>
            </head>
            <body>
                {replace_image(one[2], cur)}
                {replace_image(one[3], cur)}
            </body>
        </html>
        '''
        file = sys.path[0] + f"/article/{one[0]}.html"
        Path(file).parent.mkdir(exist_ok=True, parents=True)
        with open(file, "w+", encoding="utf-8") as f:
            f.write(page)
        cur.execute("update article set done = 1 where id = ?", (one[0], ))
        conn.commit()

def replace_image(dom: str, cur: Cursor):
    soup = BeautifulSoup(dom, "html.parser")
    for one in soup.find_all("img"):
        data = cur.execute("select id, image from images where url = ?", (one['src'],)).fetchone()
        if data:
            suffix = one['src'].split(".")[-1]
            path = Path(sys.path[0] + '/images/' + str(data[0]) + '.' + suffix)
            if not path.exists():
                path.parent.mkdir(exist_ok=True, parents=True)
                with open(sys.path[0] + '/images/' + str(data[0]) + '.' + suffix, "wb+") as f:
                    f.write(data[1])
            one['src'] = '/images/' + str(data[0]) + "." + suffix
            if one.parent.has_attr('href'):
                one.parent['href'] = '/images/' + str(data[0]) + "." + suffix
    return str(soup)
        

        

def gen_index(index=0):
    conn = sqlite3.connect(sys.path[0] + '/cnbeta.db')
    cur = conn.cursor()
    data = cur.execute('select id, title, desc from article order by id desc limit ?, 30', (index * 30, )).fetchall()
    articles = ['<h3><a href="/article/%s.html">%s</a></h3>'%(one[0], one[1]) for one in data]
    page = f'''
    <html lang="en">
        <head>
            <meta charset="utf-8">
            <title>cnbeta</title>
        </head>
        <body>
            {"".join(articles)}
            <a href="/page/{index + 1}">next</a>
        </body>
    </html>
    '''
    if index == 0:
        with open(sys.path[0] + '/index.html', "w+", encoding="utf-8") as f:
            f.write(page)
    else:
        file = sys.path[0] + f"/page/{index}/index.html"
        Path(file).parent.mkdir(exist_ok=True, parents=True)
        with open(file, "w+", encoding="utf-8") as f:
            f.write(page)
    if len(data) > 0:
        gen_index(index + 1)

if __name__ == "__main__":
    gen_index(0)
    gen_artical(False)