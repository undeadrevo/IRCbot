from bs4 import BeautifulSoup
import praw, re, requests, time

def __init__(self):
    redditAPI()

def about(self,Log):
    self.privmsg(Log['context'],'Hi, I am a WIP bot coded and owned by NewellWorldOrder (or nwo). I\'m not into conspiracy theories so don\'t even bother.')
    
def redditAPI(self):
    try:
        self.r = praw.Reddit('redFetch by u/NewellWorldOrder''Fetches reddit submission links')
        enableNSFW = self.r.get_random_subreddit(nsfw=True)
        self.redditEnabled = True
        self.redditLimit = time.mktime(time.gmtime())
    except:
        self.redditEnabled = False
    pass

def reddit(self,Log):
    curTime = self.curTime()
    if not self.redditEnabled:
        self.redditAPI()
    elif curTime - self.redditLimit <= 2:
        self.ircSend('NOTICE %s :Please wait %s second(s) due to Reddit API restrictions' % (Log['nick'], str(2 - (curTime - self.redditLimit))))
    else:
        try:
            subreddit = Log['trail'][1]
            submission = self.r.get_subreddit(subreddit).get_random_submission()
            nsfwstatus = ''
            if submission.over_18:
                nsfwstatus = '[NSFW]'
            self.privmsg(Log['context'],'07Reddit 04%s10r/%s - 12%s 14(%s)' % (nsfwstatus, subreddit, submission.title, submission.url))
        except:
            print('Error fetching subreddit')
            self.privmsg(Log['context'],'I cannot fetch this subreddit at the moment')
        self.redditLimit = time.mktime(time.gmtime())

def ud(self,Log):
    try:
        r = requests.get('http://api.urbandictionary.com/v0/define?term=%s' % '+'.join(Log['trail'][1:]))
        data = r.json()
        if data['result_type'] != 'no_results':
            definition = ' '.join(data['list'][0]['definition'].splitlines())
            truncated = ''
            if len(definition) >= 150:
                truncated = '...'
                definition = definition[:146]
            self.privmsg(Log['context'],'Urban08Dictionary 12%s - 06%s%s 10(%s)' % (data['list'][0]['word'], definition[:149], truncated, data['list'][0]['permalink']))
        else:
            self.privmsg(Log['context'],'No definition for %s' % ' '.join(Log['trail'][1:]))
    except:
        print('Error fetching definition')
        self.privmsg(Log['context'],'I cannot fetch this definition at the moment')

def google(self,Log):
    url = 'https://www.google.com/search?q=%s&btnI' % '+'.join(Log['trail'][1:])
    r = requests.get('https://www.google.com/search?q=%s&btnI' % '+'.join(Log['trail'][1:]))
    if '/search?q=%s&btnI' % '+'.join(Log['trail'][1:]) in r.url:
        self.privmsg(Log['context'],'12G04o08o12g03l04e 06[%s] 13%s' % (' '.join(Log['trail'][1:]), url))
    else:
        r2 = requests.get(r.url, timeout=2)
        soup = BeautifulSoup(r.text)
        title = soup.title.text
        if title:
            linkinfo = ' – 03%s' % title
        self.privmsg(Log['context'],'12G04o08o12g03l04e 12%s04%s 08(%s)' % (' '.join(Log['trail'][1:]), linkinfo, r.url))

def wiki(self,Log):
    search = '_'.join(Log['trail'][1:])
    url = 'http://en.wikipedia.org/wiki/%s' % search
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    title = soup.title.text
    content = soup.select('div > p')[0].text
    content = re.sub('\'','\\\'',re.sub('\\n','',re.sub('\[.*?\]','',content)))
    if content == 'Other reasons this message may be displayed:':
        self.privmsg(Log['context'],'Wikipedia 03%s – 12No article found. Maybe you could write it: 11https://en.wikipedia.org/w/index.php?title=Special:UserLogin&returnto=%s' % (title, search))
    else:
        if content == '%s may refer to:' % re.sub('http://en.wikipedia.org/wiki/','',r.url):
            r = requests.get('http://en.wikipedia.org%s' % soup.find('ul').find('li').find('a')['href'])
            soup = BeautifulSoup(r.text)
            title = soup.title.text
            content = soup.select('div > p')[0].text
            content = re.sub('\'','\\\'',re.sub('\\n','',re.sub('\[.*?\]','',content)))
        exerpt = '. '.join(content.split('. ')[:1])
        if not exerpt[-1] in '!?.':
            exerpt = exerpt + '.'
        self.privmsg(Log['context'],'Wikipedia 03%s – 12%s 11(%s)' % (title, exerpt, r.url))
