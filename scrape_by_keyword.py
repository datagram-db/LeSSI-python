#!/usr/bin/env python3
__author__ = "Giacomo Bergami"
__copyright__ = "Copyright 2020, Giacomo Bergami"
__credits__ = ["Giacomo Bergami"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Giacomo Bergami"
__email__ = "bergamigiacomo@gmail.com"
__status__ = "Production"

from bs4 import BeautifulSoup
import csv
import feedparser
import re
import requests
import datetime, dateparser
import sys, argparse, os, json
from os import path
from newsplease import NewsPlease
import requests
import concurrent.futures
from lxml.html import fromstring
import traceback
import itertools
import colorama
from colorama import Fore, Back, Style
import pytz
import argparse
import plotille
import random
import ssl
import urllib

# pip3 install certifi
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

utc = pytz.UTC
rssFeedFile = None

## No certificate settings
# ctx = ssl.create_default_context()
# ctx.check_hostname = False
# ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}
verify = False


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


## Rotating the HTTP requests while performing the scraping: you might get a close on trying to get multiple elements to analyse
def get_proxies():
    url = 'https://www.sslproxies.org/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        # Grabbing IP and corresponding PORT
        proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
        proxies.add(proxy)
    return proxies


def urlify(s):
    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)
    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '-', s)
    return s


date_minimum = '2019-10-01'
workers = 10
database = dict()
doReverse = False
backArchive = True
storeJson = False
doIgnoreInterval = False
shuffle = False
timeout = None
stopIfPresent = False

proxies = get_proxies()
colorama.init()
date_global_minimum = None


def parse_url(url):
    download_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    req = urllib.request.Request(url, None, headers)
    html = ""
    # loctx = ctx
    if not verify:
        ssl._create_default_https_context = ssl._create_unverified_context  # loctx = None
    html = urllib.request.urlopen(req, data=None, timeout=timeout).read()
    return (NewsPlease.from_html(html, url, download_date).get_serializable_dict())


def craw_from_file(filename):
    """
    This function reads the content of the csv file, and puts its content inside a DB in JSON
    """
    dkey = filename[:-15]
    dkey_dbfile = dkey + ".json"
    dkey_db = {}
    if path.exists(dkey_dbfile):
        dkey_db = json.load(open(dkey_dbfile))
    dkey_db_nextKey = 1
    if len(dkey_db) > 0:
        dkey_db_nextKey = int(max(dkey_db, key=int)) + 1
    before = len(dkey_db)
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if not (dkey in database):
                database[dkey] = set()
            else:
                database[dkey] = set(database[dkey])
            if not (row[0] in database[dkey]):
                try:
                    dkey_db[str(dkey_db_nextKey)] = parse_url(
                        row[0])  # NewsPlease.from_url(row[0], timeout=timeout).get_serializable_dict()
                    database[dkey].add(row[0])
                    print(Fore.GREEN + "Article #" + str(
                        dkey_db_nextKey) + " was parsed for '" + dkey + "'" + Style.RESET_ALL)
                    dkey_db_nextKey = dkey_db_nextKey + 1
                except Exception as e:
                    print(Fore.RED + "Error: ''" + str(e) + "'' for article at ''" + row[
                        0] + "''! downloading it as a simple text file..." + Style.RESET_ALL)
                    cont = ""
                    try:
                        r = requests.get(row[0])
                        cont = r.content
                    except:
                        None
                    file1 = open("extra/" + dkey + "__" + urlify(row[1]) + ".html", 'w')
                    file1.write(str(cont))
                    file1.close()
    json.dump(dkey_db, open(dkey_dbfile, 'w'))
    print(Fore.GREEN + " +" + str(len(dkey_db) - before) + " were saved for '" + dkey + "'" + Style.RESET_ALL)
    dump_database('db.json')


class MinimalThreaded:
    def __init__(self, dkey, db_entry):
        self.dkey = dkey
        self.db_entry = db_entry


def craw_from_file_multithreaded(filename):
    """
    This function reads the content of the csv file, and puts its content inside a DB in JSON
    """
    print(filename)
    print('-------------------')
    print('-------------------')
    dkey = filename[:-15]
    dkey_dbfile = dkey + ".json"
    dkey_db = {}
    try:
        if path.exists(dkey_dbfile):
            dkey_db = json.load(open(dkey_dbfile))
    except Exception as e:
        print("ERROR WITH: " + dkey_dbfile + " " + str(e))
        return None
    dkey_db_nextKey = 1
    localdb = set()
    if (dkey in database):
        localdb = set(database[dkey])
    if len(dkey_db) > 0:
        dkey_db_nextKey = int(max(dkey_db, key=int)) + 1
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if not (row[0] in localdb):
                try:
                    dkey_db[str(dkey_db_nextKey)] = parse_url(
                        row[0])  # NewsPlease.from_url(row[0], timeout=timeout).get_serializable_dict()
                    localdb.add(row[0])
                    print(Fore.GREEN + "Article #" + str(dkey_db_nextKey) + " was parsed" + Style.RESET_ALL)
                    dkey_db_nextKey = dkey_db_nextKey + 1
                except Exception as e:
                    print(Fore.RED + "Error: ''" + str(e) + "'' for article at ''" + row[
                        0] + "''! downloading it as a simple text file..." + Style.RESET_ALL)
                    cont = ""
                    try:
                        r = requests.get(row[0])
                        cont = r.content
                    except:
                        None
                    file1 = open("extra/" + dkey + "__" + urlify(row[1]) + ".json", 'w')
                    file1.write(str(cont))
                    file1.close()
    json.dump(dkey_db, open(dkey_dbfile, 'w'))
    dump_database('db.json')
    return MinimalThreaded(dkey, localdb)


def load_database(filename):
    """
    This function loads the main database, where each domain is associated to all the articles that were already loaded inside the mini db in json
    """
    global database
    if path.exists(filename):
        with open(filename) as json_file:
            data = json.load(json_file)
            for k in data:
                data[k] = set(data[k])
            database = data


def dump_database(filename):
    """
    This function dumps the dictionary in main memory into the fila corresponding to the main database
    """
    for k in database:
        database[k] = list(database[k])
    json.dump(database, open(filename, 'w'))


def get_all_csvs():
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in files:
        if (f.endswith('.csv')):
            craw_from_file(f)


def get_all_csvs_iterator():
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in files:
        if (f.endswith('.csv')):
            yield f


def search_article(url, phrases, proxy=None):
    """
    Yield all of the specified phrases that occur in the HTML body of the URL.
    """
    response = None
    if proxy is None:
        response = requests.get(url)
    else:
        response = requests.get(url, proxies={"http": proxy, "https": proxy})
    text = BeautifulSoup(response.text, 'html.parser').find_all('div', {"itemprop": "articleBody"})

    for phrase in phrases:
        for i in text:
            i = i.text
            block = ''
            block = block + i

            if re.search(r'\b' + re.escape(phrase) + r'\b', block):
                yield phrase


def search_rss(rss_entries, phrases, proxy=None):
    """
    Search articles listed in the RSS entries for phases, yielding
    (url, article_title, phrase) tuples.
    """
    for entry in rss_entries:
        if len(phrases) == 0:
            yield entry['link'], entry['title'], "body", "hit"
        else:
            foundInTitle = False
            for hit_phrase in phrases:
                for i in entry['title'].split():
                    if (hit_phrase.lower() == i.lower()):
                        foundInTitle = True
                        yield entry['link'], entry['title'], "title", hit_phrase
            if not (foundInTitle):
                for hit_phrase in search_article(entry['link'], phrases, proxy):
                    yield entry['link'], entry['title'], "body", hit_phrase


def url_wayback_expand(url, min_=dateparser.parse(date_minimum), max_=None):
    """
        This funciton uses the WayBack Machine from Web Archive to retrieve all the past definitions of the RSS feeds
        """
    print(Fore.YELLOW + "Attempt at wayback-expanding " + url + " ..." + Style.RESET_ALL)
    r = requests.get("http://web.archive.org/web/timemap/link/" + url, timeout=timeout)
    l = str(r.content).split('\\n')[1:]
    if doReverse: l.reverse()
    dateSet = set()
    for entry in l:
        l = list(map(lambda x: x.strip(), entry.split(';')))
        if (len(l) < 3):
            continue
        url = l[0][1:-1]
        date = l[-1].split('=')[1:][0].split("\"")[1]
        date = dateparser.parse(date).replace(tzinfo=utc)
        date2 = date.replace(hour=0, minute=0, second=0, microsecond=0)
        if date2 in dateSet: continue  # Reducing the URLs to analyse: it simplifies the download and the attempts at parsing some data...
        dateSet.add(date2)
        if (min_.replace(tzinfo=utc) <= date):
            if doIgnoreInterval:
                yield (date, url)
            elif max_ is None:
                yield (date, url)
            elif (max_.replace(tzinfo=utc) >= date):
                yield (date, url)
    # sorting the


# def single_url_dump(rss_url, phrases, output_csv_path, visited_papers):
#    rss_entries = feedparser.parse(rss_url).entries[:None]
#    print(output_csv_path)
#    dkey = output_csv_path[:-15]
#    print("--------------------")
#    print("--------------------")
#    with open(output_csv_path, 'w') as f:
#        w = csv.writer(f)
#        for url, title, src, phrase in search_rss(rss_entries, phrases):
#            if url in visited_papers: continue
#            if not (dkey in database): database[dkey] = set()
#            if not (url in database[dkey]):         
#                    print(Fore.CYAN+'"{0}" found in "{1}" from "{2}"'.format(phrase, title, src)+Style.RESET_ALL)
#                    w.writerow([url, title])
#                    f.flush()
#        f.close()
#    return(visited_papers)
#                    
# def main(rss_url, phrases, output_csv_path, goBack=False):
#    visited_papers = set() # Not adding to the csv file the same article multiple times
#    visited_papers = single_url_dump(rss_url, phrases, output_csv_path, visited_papers)
#    if goBack:
#      for (url, date) in url_wayback_expand(rss_url):
#        print(Fore.YELLOW+rss_url+" going back in time: @"+date+Style.RESET_ALL)
#        visited_papers = single_url_dump(url, phrases, output_csv_path, visited_papers)

def plot_list(f, ll):
    print()
    print()
    print("--------------------------------------------------------------")
    print(f)
    print("--------------------------------------------------------------")
    if (len(ll) > 0): print(
        plotille.histogram(ll, X_label='Dates', x_min=dateparser.parse(date_minimum).replace(tzinfo=utc),
                           x_max=datetime.datetime.today().replace(tzinfo=utc)))
    print("--------------------------------------------------------------")


def plot_jsons(f, doPlot=False):
    ll = []
    l = json.load(open(f))
    for k in l:
        art = dateparser.parse(l[k]["date_publish"])
        if (art is None):
            continue
        ll.append(art.replace(tzinfo=utc))
    if doPlot: plot_list(f, ll)
    return ll


def detectMins(f):
    """
       Given a file information, it detects which is the biggest interval containing the most papers to be parsed, and retrieves such content.
       Python is not very good at handling resources: this simple loading code will load a massive amount of data into primary memory... Need to change this
       """
    global date_global_minimum
    ll = []
    min_ = date_global_minimum.replace(tzinfo=utc)
    day = datetime.datetime.today().replace(tzinfo=utc)
    max_ = datetime.datetime(day.year, day.month, day.day, 23, 59, 59).replace(tzinfo=utc)
    if not (path.exists(f)): return (min_, max_)
    l = json.load(open(f))
    for k in l:
        art = dateparser.parse(l[k]["date_publish"])
        if (art is None):
            continue
        art = art.replace(tzinfo=utc)
        ll.append(art)
        if (art < day) and (art > date_global_minimum):
            fromFile = f
            day = art
    ll = filter(
        lambda x: x >= date_global_minimum.replace(tzinfo=utc) and x <= datetime.datetime.today().replace(tzinfo=utc),
        ll)
    ll = sorted(list(dict.fromkeys(filter(lambda x: x is not None, ll))))
    if (len(ll) == 1):
        if (ll[0] == day):
            min_ = datetime.datetime(ll[0].year, ll[0].month, ll[0].day, 0, 0, 0).replace(tzinfo=utc)
    elif (len(ll) > 1):
        cpCand_withScore = max(map(lambda x: ((x[1] - x[0]).total_seconds(), x), zip(ll[:-1], ll[1:])),
                               key=lambda x: x[0])
        lt = [cpCand_withScore, ((ll[0] - date_global_minimum).total_seconds(), (date_global_minimum, ll[0])),
              ((day - ll[-1]).total_seconds(), (min(ll[-1], day), max(ll[-1], day)))]
        cpCand = max(lt, key=lambda x: x[0])
        min_ = cpCand[1][0]
        max_ = cpCand[1][
            1]  # from"+str(list(map(lambda x:str(x[0])+",("+x[1][0].strftime('%Y-%m-%d %HH-%mm')+" ~ "+x[1][1].strftime('%Y-%m-%d %HH-%mm')+")", lt)))+" and min= "+ll[0].strftime('%Y-%m-%d %HH-%mm')+Style.RESET_ALL)
    if not doIgnoreInterval: min_ = max(min_, date_global_minimum.replace(tzinfo=utc))
    max_ = min(max_, datetime.datetime.today().replace(tzinfo=utc))
    print(Fore.YELLOW + f + ": detected Time Interval = {" + min_.strftime('%Y-%m-%d %HH-%mm') + "," + max_.strftime(
        '%Y-%m-%d %HH-%mm') + "}" + Style.RESET_ALL)
    return (min_, max_)


def lastStats():
    """
 THis file prints some stats, where it is shown which is the latest content for each domain
 """
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in files:
        if (f.endswith('.json')) and (not (f == 'db.json')):
            fromFile = "None"
            day = datetime.datetime.today()
            l = json.load(open(f))
            for k in l:
                art = dateparser.parse(l[k]["date_publish"])
                if art is None: continue
                if (art < day) and (art > dateparser.parse(date_minimum)):
                    fromFile = f
                    day = art
            print("Earliest day found was " + day.strftime('%Y-%m-%d') + " from " + fromFile)


def multithread_run(rss_url, phrases, output_csv_path, database, proxies, goBack):
    """
    Uses the NewsThread class to load the content
    """
    obj = NewsThread(rss_url, phrases, output_csv_path, database, proxies, goBack)
    obj.run()
    return obj


class NewsThread:
    def __init__(self, rss_url, phrases, output_csv_path, database, proxies, goBack=False):
        self.rss_url = rss_url
        self.phrases = phrases
        self.output_csv_path = output_csv_path
        self.goBack = goBack
        self.visited_papers = set()  # Not adding to the csv file the same article multiple times
        self.dkey = self.output_csv_path[:-15]
        self.byline_json = self.dkey + ".lsjson"
        if not (self.dkey in database):
            self.db_entry = set()
        else:
            self.db_entry = set(database[self.dkey])
        self.dkey_dbfile = self.dkey+".json"                        #-- Legacy article storage
        # self.date_cp = detectMins(self.dkey_dbfile)
        ##self.dkey_db_nextKey = 1                                    -- Legacy article storage
        ##self.dkey_db = {}                                           -- Legacy article storage
        self.proxies = itertools.cycle(proxies)
        self.wasError = False
        self.dateLimits = detectMins(self.dkey_dbfile)            #-- Temporairly disabling this part of the code
        ##if path.exists(self.dkey_dbfile):                         -- Legacy article storage
        ##    self.dkey_db = json.load(open(self.dkey_dbfile))      -- Legacy article storage
        ##if len(self.dkey_db) > 0:                                 -- Legacy article storage
        ##    self.dkey_db_nextKey = int(max(self.dkey_db,key=int))+1   -- Legacy article storage

    def single_url_dump(self, rss_url):
        """
        This function stores inside a csv file all the relevant URLS do be parsed in the next step
        """
        global stopIfPresent
        if self.wasError:
            return (False)
        rss_entries = feedparser.parse(rss_url).entries[:None]
        skipCount = 0
        elementsInList = []
        try:
            for url, title, src, phrase in search_rss(rss_entries, self.phrases, None):
                if url in self.visited_papers:
                    skipCount = skipCount + 1
                    continue
                self.visited_papers.add(url)
                if not (url in self.db_entry):
                    print(Fore.CYAN + '"{0}" found in "{1}" from "{2}@{3}"'.format(phrase, title, src,
                                                                                   rss_url) + Style.RESET_ALL)
                    elementsInList.append([url, title])
                else:
                    skipCount = skipCount + 1
        except Exception as exc:
            print(Fore.RED + '%r generated an exception: %s' % (str(self.rss_url), exc) + Style.RESET_ALL)
            traceback.print_exc()
            self.wasError = True
        self.f = open(self.output_csv_path, 'a')
        self.w = csv.writer(self.f)
        for ls in elementsInList:
            self.w.writerow(ls)
            self.f.flush()
        self.f.close()
        print(Fore.GREEN + '{0} articles were skipped for {1}"'.format(str(skipCount), rss_url) + Style.RESET_ALL)
        # print(stopIfPresent)
        if not stopIfPresent:
            skipCount = 0
        return (stopIfPresent and (skipCount > 0))

    def main(self):
        """
        This function parses the main RSS file and, if possible (goBack) also parses different RSS back in time
        """
        self.single_url_dump(self.rss_url)
        if self.goBack:
            letitbe_min = min(self.dateLimits)
            letitbe_max = max(self.dateLimits)
            for (date, url) in url_wayback_expand(
                    self.rss_url):  # url_wayback_expand(self.rss_url, letitbe_min, letitbe_max)
                print(Fore.YELLOW + self.rss_url + " going back in time: @" + str(date) + Style.RESET_ALL)
                if self.single_url_dump(url) and (not doReverse): break

    def craw_from_file(self):
        """
      Given the information stored in the CSV file, this function parses the article and stores it in the local database
      """
        append_file = open(self.byline_json, "a")
        print(Fore.GREEN + "APPEND FILE OPENEND: " + self.byline_json + Style.RESET_ALL)
        with open(self.output_csv_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not (row[0] in self.db_entry):
                    try:
                        # self.dkey_db[str(self.dkey_db_nextKey)] = parse_url(row[0])#NewsPlease.from_url(row[0], timeout=timeout).get_serializable_dict()
                        append_file.write(parse_url(row[0]) + "\n")
                        self.db_entry.add(row[0])
                        print(Fore.GREEN + self.output_csv_path + ": Article #" + str(
                            self.dkey_db_nextKey) + " was parsed" + Style.RESET_ALL)
                        # self.dkey_db_nextKey = self.dkey_db_nextKey+1

                    except Exception as e:
                        print(Fore.RED + "Error: ''" + str(e) + "'' for article at ''" + row[
                            0] + "''! downloading it as a simple text file..." + Style.RESET_ALL)
                        cont = ""
                        try:
                            r = requests.get(row[0], verify=False)
                            cont = r.content
                        except:
                            None
                        file1 = open("extra/" + self.dkey + "__" + urlify(row[1]) + ".html", 'w')
                        file1.write(str(cont))
                        file1.close()
        append_file.close()
        ##json.dump(self.dkey_db,open(self.dkey_dbfile,'w'))  -- Legacy

    def run(self):
        """
        Performs the parsing of the RSS, and then uploads the content of each detected valid article into the DB in json
        """
        global storeJson
        self.main()
        if storeJson: self.craw_from_file()


def run_sequentially(self):
    """
    This function accepts a NewsThread that was already run, and updates the global database with the novel downloaded content
    """
    global database
    database[self.dkey] = list(self.db_entry)


# def url_list_small(day):
#     return [#('https://www.dailymail.co.uk/sciencetech/index.rss',  'dailymail_sci_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/world/asia/rss.xml',  'bbc_asia_'+day+'.csv'),
#     #('http://feeds.foxnews.com/foxnews/health',  'fox_hea_'+day+'.csv'),
#     #('https://www.theguardian.com/uk/technology/rss', 'theguardian_'+day+'.csv'),
#     #('http://www.independent.co.uk/news/world/rss',  'indep_world_'+day+'.csv'),
#     ('https://rss.nytimes.com/services/xml/rss/nyt/Health.xml',  'nyt_health_'+day+'.csv'),
#     ('https://www.latimes.com/california/rss2.0.xml',  'lat_cali_'+day+'.csv'),
#     #('http://news.yahoo.com/rss/',  'yahoo_'+day+'.csv'),
#     ('http://feeds.reuters.com/Reuters/domesticNews',  'reuters_'+day+'.csv'),
#     ('https://www.huffpost.com/section/healthy-living/feed', 'huff_hea_'+day+'.csv'),
#
#     #('https://www.theguardian.com/world/rss', 'theguardian_world_'+day+'.csv'),
#     #('https://www.dailymail.co.uk/home/index.rss',  'dailymail_uk_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/world/europe/rss.xml',  'bbc_eu_'+day+'.csv'),
#     #('http://feeds.foxnews.com/foxnews/science',  'fox_sci_'+day+'.csv'),
#     #('http://www.independent.co.uk/news/science/rss',  'indep_science_'+day+'.csv'),
#     ('https://rss.nytimes.com/services/xml/rss/nyt/NYRegion.xml',  'nyt_region_'+day+'.csv'),
#     ('https://www.latimes.com/world-nation/rss2.0.xml',  'lat_wonat_'+day+'.csv'),
#     #('https://www.huffpost.com/section/health/feed', 'huff_hea2_'+day+'.csv'),
#
#     #('https://www.theguardian.com/tone/obituaries/rss', 'theguardian_obit_'+day+'.csv'),
#     #('https://www.dailymail.co.uk/news/index.rss',  'dailymail_news_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml',  'bbc_usca_'+day+'.csv'),
#     #('http://feeds.foxnews.com/foxnews/world',  'fox_world_'+day+'.csv'),
#     #('http://www.independent.co.uk/news/obituaries/rss',  'indep_death_'+day+'.csv'),
#     ('https://rss.nytimes.com/services/xml/rss/nyt/Obituaries.xml',  'nyt_death_'+day+'.csv'),
#     ('https://www.huffpost.com/section/front-page/feed', 'huff_main_'+day+'.csv'),
#
#     #('https://www.theguardian.com/world/coronavirus-outbreak/rss', 'theguardian_corona_'+day+'.csv'),
#     #('https://www.dailymail.co.uk/ushome/index.rss',  'dailymail_us_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/video_and_audio/world/rss.xml',  'bbc_world_'+day+'.csv'),
#     #('http://feeds.foxnews.com/foxnews/national',  'fox_us_'+day+'.csv'),
#     #('http://www.independent.co.uk/news/uk/rss',  'indep_uk_'+day+'.csv'),
#     ('https://rss.nytimes.com/services/xml/rss/nyt/Science.xml',  'nyt_sci_'+day+'.csv'),
#     ('https://www.huffpost.com/section/politics/feed', 'huff_pol_'+day+".csv"),
#
#     #('https://www.theguardian.com/uk/rss','theguardian_uk_'+day+'.csv'),
#     #('https://www.dailymail.co.uk/health/index.rss',  'dailymail_hea_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/video_and_audio/uk/rss.xml',  'bbc_uk_'+day+'.csv'),
#     ('https://rss.nytimes.com/services/xml/rss/nyt/US.xml',  'nyt_us_'+day+'.csv'),
#     ('https://www.huffpost.com/section/opinion/feed', 'huff_op_'+day+".csv"),
#
#     #('https://www.theguardian.com/us/rss','theguardian_us_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/video_and_audio/health/rss.xml',  'bbc_hea_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/video_and_audio/science_and_environment/rss.xml',  'bbc_sci_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/rss.xml',  'bbc_'+day+'.csv')#,
#     #('https://rss.nytimes.com/services/xml/rss/nyt/World.xml',  'nyt_world_'+day+'.csv'),
#     #('https://www.huffpost.com/section/world-news/feed', 'huff_op_'+day+".csv")
#     ]
#
def url_list(day):
    lst = []
    with open(rssFeedFile) as f:
        reader = csv.reader(f)
        for line in reader:
            import string
            line[1] = str(string.Template(line[1]).safe_substitute({'day':day}))
            lst.append(tuple(line))
    return lst

#     return [('https://www.dailymail.co.uk/sciencetech/index.rss',  'dailymail_sci_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/world/asia/rss.xml',  'bbc_asia_'+day+'.csv'),
#     ('http://feeds.foxnews.com/foxnews/health',  'fox_hea_'+day+'.csv'),
#     ('https://www.theguardian.com/uk/technology/rss', 'theguardian_'+day+'.csv'),
#     ('http://www.independent.co.uk/news/world/rss',  'indep_world_'+day+'.csv'),
#     ('https://rss.nytimes.com/services/xml/rss/nyt/Health.xml',  'nyt_health_'+day+'.csv'),
#     ('https://www.latimes.com/california/rss2.0.xml',  'lat_cali_'+day+'.csv'),
#     ('http://news.yahoo.com/rss/',  'yahoo_'+day+'.csv'),
#     ('http://feeds.reuters.com/Reuters/domesticNews',  'reuters_'+day+'.csv'),
#     ('https://www.huffpost.com/section/healthy-living/feed', 'huff_hea_'+day+'.csv'),
#
#     ('https://www.theguardian.com/world/rss', 'theguardian_world_'+day+'.csv'),
#     ('https://www.dailymail.co.uk/home/index.rss',  'dailymail_uk_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/world/europe/rss.xml',  'bbc_eu_'+day+'.csv'),
#     ('http://feeds.foxnews.com/foxnews/science',  'fox_sci_'+day+'.csv'),
#     ('http://www.independent.co.uk/news/science/rss',  'indep_science_'+day+'.csv'),
#     ('https://rss.nytimes.com/services/xml/rss/nyt/NYRegion.xml',  'nyt_region_'+day+'.csv'),
#     ('https://www.latimes.com/world-nation/rss2.0.xml',  'lat_wonat_'+day+'.csv'),
#     ('https://www.huffpost.com/section/health/feed', 'huff_hea2_'+day+'.csv'),
#
#     ('https://www.theguardian.com/tone/obituaries/rss', 'theguardian_obit_'+day+'.csv'),
#     ('https://www.dailymail.co.uk/news/index.rss',  'dailymail_news_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml',  'bbc_usca_'+day+'.csv'),
#     ('http://feeds.foxnews.com/foxnews/world',  'fox_world_'+day+'.csv'),
#     ('http://www.independent.co.uk/news/obituaries/rss',  'indep_death_'+day+'.csv'),
#     ('https://rss.nytimes.com/services/xml/rss/nyt/Obituaries.xml',  'nyt_death_'+day+'.csv'),
#     ('https://www.huffpost.com/section/front-page/feed', 'huff_main_'+day+'.csv'),
#
#     ('https://www.theguardian.com/world/coronavirus-outbreak/rss', 'theguardian_corona_'+day+'.csv'),
#     ('https://www.dailymail.co.uk/ushome/index.rss',  'dailymail_us_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/video_and_audio/world/rss.xml',  'bbc_world_'+day+'.csv'),
#     ('http://feeds.foxnews.com/foxnews/national',  'fox_us_'+day+'.csv'),
#     ('http://www.independent.co.uk/news/uk/rss',  'indep_uk_'+day+'.csv'),
#     ('https://rss.nytimes.com/services/xml/rss/nyt/Science.xml',  'nyt_sci_'+day+'.csv'),
#     ('https://www.huffpost.com/section/politics/feed', 'huff_pol_'+day+".csv"),
#
#     ('https://www.theguardian.com/uk/rss','theguardian_uk_'+day+'.csv'),
#     ('https://www.dailymail.co.uk/health/index.rss',  'dailymail_hea_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/video_and_audio/uk/rss.xml',  'bbc_uk_'+day+'.csv'),
#     ('https://rss.nytimes.com/services/xml/rss/nyt/US.xml',  'nyt_us_'+day+'.csv'),
#     ('https://www.huffpost.com/section/opinion/feed', 'huff_op_'+day+".csv"),
#
#     ('https://www.theguardian.com/us/rss','theguardian_us_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/video_and_audio/health/rss.xml',  'bbc_hea_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/video_and_audio/science_and_environment/rss.xml',  'bbc_sci_'+day+'.csv'),
#     ('http://feeds.bbci.co.uk/news/rss.xml',  'bbc_'+day+'.csv'),
#     ('https://rss.nytimes.com/services/xml/rss/nyt/World.xml',  'nyt_world_'+day+'.csv'),
#     ('https://www.huffpost.com/section/world-news/feed', 'huff_op_'+day+".csv")]

phrases = [] #['coronavirus', 'covid-19', 'covid', 'SARS-CoV-2']

# rss_url, phrases, output_csv_path, database, proxies, goBack)

# def multirun():
#  day = datetime.datetime.today().strftime('%Y-%m-%d')
#  URLS = url_list(day)
#  random.seed(datetime.datetime.now())
#  if shuffle: random.shuffle(URLS)
#  with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
#     # Start the load operations and mark each future with its URL
#     future_to_url = {executor.submit(main, x, phrases, y, backArchive): (x,y) for (x,y) in URLS}
#     for future in concurrent.futures.as_completed(future_to_url):
#         url = future_to_url[future]
#         try:
#             data = future.result()
#         except Exception as exc:
#             print('[Multirun] %r generated an exception: %s' % (str(url), exc))
#         else:
#             print('[Multirun] Articles from %r were downloaded' % (str(url)))

def multirun2():
    day = datetime.datetime.today().strftime('%Y-%m-%d')
    URLS = url_list(day)
    if shuffle: random.shuffle(URLS)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(multithread_run, x, phrases, y, database, proxies, backArchive): (x, y) for
                         (x, y) in URLS}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
                run_sequentially(data)  # dumping at the end inside the database
            except Exception as exc:
                print(Fore.RED + ('[Multirun2] %r generated an exception: %s' % (str(url), exc)) + Style.RESET_ALL)
                print(traceback.format_exc())
            else:
                print(Fore.GREEN + ('[Multirun2] Articles from %r were downloaded' % (str(url))) + Style.RESET_ALL)


def multithread_crawl(rss_url, phrases, output_csv_path, database, proxies, goBack):
    """
    Uses the NewsThread class to load the content
    """
    obj = NewsThread(rss_url, phrases, output_csv_path, database, proxies, goBack)
    obj.craw_from_file()
    return obj


def multi_crawl():
    day = datetime.datetime.today().strftime('%Y-%m-%d')
    URLS = url_list(day)
    if shuffle: random.shuffle(URLS)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(craw_from_file_multithreaded, f): f for f in get_all_csvs_iterator()}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
                run_sequentially(data)  # dumping at the end inside the database
            except Exception as exc:
                print(Fore.RED + ('[multi_crawl] %r generated an exception: %s' % (str(url), exc)) + Style.RESET_ALL)
                print(traceback.format_exc())
            else:
                print(Fore.GREEN + ('[multi_crawl] Articles from %r were loaded in the local database!' % (
                    str(url))) + Style.RESET_ALL)


if __name__ == '__main__':
    import os
    if not os.path.exists('extra'):
        os.makedirs('extra')
    parser = argparse.ArgumentParser(description="Scrape by Keyword: scraping the online news via Python.")
    parser.add_argument('-k', '--keywords', nargs='+', default=[])
    parser.add_argument("--RSSFeedCsv", default=False, type=str,
                        help="Defines the configuration csv file containing the rss feed from the newspapers")
    parser.add_argument('--store_json', default=False, action='store_true',
                        help="Loads the articles temporarly stored into a csv file directly to the mini json database")
    parser.add_argument('--ignore_intervals', default=False, action='store_true',
                        help="Instead of scraping the articles from the biggest information gap found, it scrapes all the articles starting from the minimum date")
    parser.add_argument('--back_archive', default=False, action='store_true',
                        help="Uses the wayback engine to retrieve the RSS feed from the past")
    parser.add_argument('--min_date', default="2019-10-01", type=str,
                        help="Minimum date in the yyyy-mm-dd format from which you need to scrape the articles")
    parser.add_argument('--threads', default=10, type=int,
                        help="The minimum amount of threads to be used in the scraping")
    parser.add_argument('--shuffle', default=False, action='store_true',
                        help="Shuffles the list used to do the crawling")
    parser.add_argument('--timeout', default=None, type=int,
                        help="Sets the timeouts when crawling obsessively, so the scripts doesn't hang up (in seconds)")
    parser.add_argument('--reverse', default=False, action='store_true',
                        help="Gets the information from the most recent to the oldest when using the back_archive (flag needs to be activated)")
    parser.add_argument('--no_ssl', default=True, action='store_false', help="Disables SSL Checking")
    parser.add_argument('--no_stop_if_parsed', default=True, action='store_false',
                        help="Stops from crawling back in time when you hit some day were some articles were already dowloaded")
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    backArchive = args.back_archive
    phrases = args.keywords
    doIgnoreInterval = args.ignore_intervals
    date_minimum = args.min_date
    rssFeedFile = args.RSSFeedCsv
    date_global_minimum = dateparser.parse(date_minimum).replace(tzinfo=utc)
    storeJson = args.store_json
    timeout = args.timeout
    shuffle = args.shuffle
    workers = args.threads
    stopIfPresent = args.no_stop_if_parsed
    doReverse = args.reverse
    verify = args.no_ssl
    load_database('db.json')
    multirun2()
    # get_all_csvs() --> This is replaced by running the loader in each single thead!
    dump_database('db.json')
    # lastStats()
