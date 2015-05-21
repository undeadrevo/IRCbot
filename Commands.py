# coding=utf8

from bs4 import BeautifulSoup
import praw, re, requests, time

commands = {}

def about(self,Log):
    self.PRIVMSG(Log['context'],'Hi, I am a WIP bot coded and owned by NewellWorldOrder (or nwo). I\'m not into conspiracy theories so don\'t even bother.')
commands['!about'] = about
    
# returns active users
def active(self,Log):
    if len(self.listActive(Log['context'])) == 1:
        self.PRIVMSG(Log['context'],'There is 1 active user here (only users identified with NickServ are included)')
    else:
        self.PRIVMSG(Log['context'],'There are %s active users in here (only users identified with NickServ are included)' % len(self.listActive(Log['context'])))
commands['!active'] = active
    
def redditAPI(self):
    try:
        self.r = praw.Reddit('redFetch by u/NewellWorldOrder''Fetches reddit submission links')
        enableNSFW = self.r.get_random_subreddit(nsfw=True)
        self.redditEnabled = True
        self.redditLimit = time.mktime(time.gmtime())
    except:
        self.redditEnabled = False

def reddit(self,Log):
    timenow = time.mktime(time.gmtime())
    if not self.redditEnabled:
        self.redditAPI()
    elif timenow - self.redditLimit <= 2:
        self.ircSend('NOTICE %s :Please wait %s second(s) due to Reddit API restrictions' % (Log['nick'], str(2 - (timenow - self.redditLimit))))
    else:
        try:
            subreddit = Log['trail'][1]
            submission = self.r.get_subreddit(subreddit).get_random_submission()
            nsfwstatus = ''
            if submission.over_18:
                nsfwstatus = '[NSFW]'
            self.PRIVMSG(Log['context'],'07Reddit 04%s10r/%s - 12%s 14(%s)' % (nsfwstatus, subreddit, submission.title, submission.url))
        except:
            print('Error fetching subreddit')
            self.PRIVMSG(Log['context'],'I cannot fetch this subreddit at the moment')
        self.redditLimit = timenow
commands['!reddit'] = reddit

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
            self.PRIVMSG(Log['context'],'Urban08Dictionary 12%s - 06%s%s 10(%s)' % (data['list'][0]['word'], definition[:149], truncated, data['list'][0]['permalink']))
        else:
            self.PRIVMSG(Log['context'],'No definition for %s' % ' '.join(Log['trail'][1:]))
    except:
        print('Error fetching definition')
        self.PRIVMSG(Log['context'],'I cannot fetch this definition at the moment')
commands['!ud'] = ud

def google(self,Log):
    url = 'https://www.google.com/search?q=%s&btnI' % '+'.join(Log['trail'][1:])
    r = requests.get('https://www.google.com/search?q=%s&btnI' % '+'.join(Log['trail'][1:]))
    if '/search?q=%s&btnI' % '+'.join(Log['trail'][1:]) in r.url:
        self.PRIVMSG(Log['context'],'12G04o08o12g03l04e 06[%s] 13%s' % (' '.join(Log['trail'][1:]), url))
    else:
        r2 = requests.get(r.url, timeout=2)
        soup = BeautifulSoup(r.text)
        title = soup.title.text
        if title:
            linkinfo = ' – 03%s' % title
        self.PRIVMSG(Log['context'],'12G04o08o12g03l04e 12%s04%s 08(%s)' % (' '.join(Log['trail'][1:]), linkinfo, r.url))
commands['!google'] = google

def wiki(self,Log):
    search = '_'.join(Log['trail'][1:])
    url = 'http://en.wikipedia.org/wiki/%s' % search
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    title = soup.title.text
    content = soup.select('div > p')[0].text
    content = re.sub('\'','\\\'',re.sub('\\n','',re.sub('\[.*?\]','',content)))
    if content == 'Other reasons this message may be displayed:':
        self.PRIVMSG(Log['context'],'Wikipedia 03%s – 12No article found. Maybe you could write it: 11https://en.wikipedia.org/w/index.php?title=Special:UserLogin&returnto=%s' % (title, search))
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
        self.PRIVMSG(Log['context'],'Wikipedia 03%s – 12%s 11(%s)' % (title, exerpt, r.url))
commands['!wiki'] = wiki

def Handler(self,Log):
    if Log['trail'][0].lower() in commands.keys():
        try:
            commands[Log['trail'][0].lower()](self,Log)
        except IndexError:
            self.ircSend('NOTICE %s :Invalid input for $s' % (Log['nick'],Log['trail'][0].lower()))