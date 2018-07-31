import requests
from bs4 import BeautifulSoup
import sqlite3
import os.path
# import pdb


start_url = 'https://www.guancha.cn'


def create_searching_list() -> list:
    res = requests.get(start_url)
    res.raise_for_status()
    res.encoding = 'utf-8'
    news_list = []
    soup = BeautifulSoup(res.text, 'html.parser')
    # print(soup.prettify())

    headline_url_a = soup.select('div.content-headline > h3 > a')[0]
    headline_url = start_url + headline_url_a['href']
    headline_title = headline_url_a.text

    news_list.append({'url': headline_url, 'title': headline_title})

    title_h4_a = soup.select('h4.module-title > a')
    for a in title_h4_a:
        url = start_url + a['href']
        title = a.text
        news_list.append({'url': url, 'title': title})
    return news_list


def get_news_content(response) -> str:
    soup = BeautifulSoup(response.text, 'html.parser')

    content_p = soup.select('div.content.all-txt > p')
    if not content_p:
        script_tags = soup.select('script')
        for script in script_tags:
            if script.text.strip().startswith('window.location.href="'):
                redirect_url = script.text.strip().split('"')[1]
                # print(redirect_url)
                res = requests.get(redirect_url)
                res.raise_for_status()
                res.encoding = 'utf-8'
                soup = BeautifulSoup(res.text, 'html.parser')
                # pdb.set_trace()
                content_p = soup.select('div.article-txt > p')
                break
    else:
        # pdb.set_trace()
        if soup.select('div.module-page > a.last'):
            remainder_all_url = response.url.split('.shtml')[0] + '_s.shtml'
            # print(remainder_all_url)
            res = requests.get(remainder_all_url)
            res.raise_for_status()
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
        content_p = soup.select('div.content.all-txt > p')

    news_content = ''
    for p in content_p:
        news_content += (p.text + '\n')
    return news_content


def get_news_datetime(response) -> str:
    soup = BeautifulSoup(response.text, 'html.parser')
    time_span = soup.select('div.time.fix > span')

    return time_span[0].text


def init_db():
    conn = sqlite3.connect('guancha.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE news
                 (p_ID integer primary key autoincrement, date_time text, title text, content text, url text)''')
    conn.commit()
    conn.close()


def connect_db(db_name):
    conn = sqlite3.connect(db_name)
    return conn


def write_news_db(conn, news_date_time, news_title, news_content, news_url):
    c = conn.cursor()
    c.execute("INSERT INTO news (p_ID, date_time, title, content, url) VALUES (NULL, ?, ?, ?, ?)", 
              (news_date_time, news_title, news_content, news_url))


def close_db(conn):
    conn.commit()
    conn.close()


if __name__ == '__main__':
    if not os.path.exists('guancha.db'):
        init_db()
    db = connect_db('guancha.db')
    for index, news in enumerate(create_searching_list()):
        print(index, news['title'])
        rv = requests.get(news['url'])
        rv.raise_for_status()
        rv.encoding = 'utf-8'

        date_time = get_news_datetime(rv)
        content = get_news_content(rv)
        write_news_db(conn=db, news_date_time=date_time, news_title=news['title'],
                      news_content=content, news_url=news['url'])
    close_db(db)
