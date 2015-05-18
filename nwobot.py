#!/usr/bin/env python
# coding=utf8

from bs4 import BeautifulSoup
from operator import itemgetter
import base64, praw, re, requests, socket, ssl, time

# Author = Brian W.

class setup:
    def __init__(self):
        yesorno = input("Do you want to write a new configuration file? y/N: ")
        if 'y' in yesorno.lower():
            while True:
                newinfo = {}
                newinfo['HOST'] = input("\nEnter the IRC network that the bot should join: ")
                newinfo['PORT'] = input("Enter the port that the bot should connect with: ")
                newinfo['NICK'] = input("Enter the nickname that the bot should use: ")
                newinfo['SASL'] = input("Do you to authenticate using SASL? (y/N): ")
                newinfo['PASS'] = input("Enter the password that the bot will authenticate with (if applicable): ")
                newinfo['NAME'] = input("Enter the realname that the bot should have: ")
                newinfo['CHAN'] = input("Enter the channels that the bot should join (comma separated): ")
                newinfo['IGNORE'] = input("Enter the nicks that the bot should ignore (comma separated): ")
                newinfo['OWNER'] = input("Enter the hosts of the owner(s) (comma separated): ")
                newinfo['SUDOER'] = input("Enter the hosts to receive extra privileges (comma separated): ")
                newinfo['YTAPI'] = input("Enter your YouTube Google API key: ")
                print("\n%s" % self.newinfo)
                confirm = input("\n Confirm? y/N: ")
                if 'y' in confirm.lower():
                    break
            with open('nwobot.conf', 'w+') as file:
                file.write(str(newinfo))
            with open('users.txt', 'w+') as file:
                userlist = {}
                file.write(str(userlist))

class reddit:
    def __init__(self):
        redditAPI()
    
    def redditAPI(self):
        try:
            self.r = praw.Reddit('redFetch by u/NewellWorldOrder''Fetches reddit submission links')
            enableNSFW = self.r.get_random_subreddit(nsfw=True)
            self.redditEnabled = True
            self.redditLimit = time.mktime(time.gmtime())
        except:
            self.redditEnabled = False
        pass
    
    def command(self,msgrecv):
        curTime = self.curTime()
        if not self.redditEnabled:
            self.redditAPI()
        elif curTime - self.redditLimit <= 2:
            self.ircSend('NOTICE %s :Please wait %s second(s) due to Reddit API restrictions' % (msgrecv['nick'], str(2 - (curTime - self.redditLimit))))
        else:
            try:
                subreddit = msgrecv['trail'][1]
                submission = self.r.get_subreddit(subreddit).get_random_submission()
                nsfwstatus = ''
                if submission.over_18:
                    nsfwstatus = '[NSFW]'
                self.privmsg(msgrecv['context'],'07Reddit 04%s10r/%s - 12%s 14(%s)' % (nsfwstatus, subreddit, submission.title, submission.url))
            except:
                print('Error fetching subreddit')
                self.privmsg(msgrecv['context'],'I cannot fetch this subreddit at the moment')
            self.redditLimit = time.mktime(time.gmtime())
            
class ud:
    def command(self,msgrecv):
        try:
            r = requests.get('http://api.urbandictionary.com/v0/define?term=%s' % '+'.join(msgrecv['trail'][1:]))
            data = r.json()
            if data['result_type'] != 'no_results':
                definition = ' '.join(data['list'][0]['definition'].splitlines())
                truncated = ''
                if len(definition) >= 150:
                    truncated = '...'
                    definition = definition[:146]
                self.privmsg(msgrecv['context'],'Urban08Dictionary 12%s - 06%s%s 10(%s)' % (data['list'][0]['word'], definition[:149], truncated, data['list'][0]['permalink']))
            else:
                self.privmsg(msgrecv['context'],'No definition for %s' % ' '.join(msgrecv['trail'][1:]))
        except:
            print('Error fetching definition')
            self.privmsg(msgrecv['context'],'I cannot fetch this definition at the moment')
            
class google:
    def command(self,msgrecv):
        url = 'https://www.google.com/search?q=%s&btnI' % '+'.join(msgrecv['trail'][1:])
        r = requests.get('https://www.google.com/search?q=%s&btnI' % '+'.join(msgrecv['trail'][1:]))
        if '/search?q=%s&btnI' % '+'.join(msgrecv['trail'][1:]) in r.url:
            self.privmsg(msgrecv['context'],'12G04o08o12g03l04e 06[%s] 13%s' % (' '.join(msgrecv['trail'][1:]), url))
        else:
            r2 = requests.get(r.url, timeout=2)
            soup = BeautifulSoup(r.text)
            title = soup.title.text
            if title:
                linkinfo = ' – 03%s' % title
            self.privmsg(msgrecv['context'],'12G04o08o12g03l04e 12%s04%s 08(%s)' % (' '.join(msgrecv['trail'][1:]), linkinfo, r.url))
            
class wiki:
    def command(self,msgrecv):
        search = '_'.join(msgrecv['trail'][1:])
        url = 'http://en.wikipedia.org/wiki/%s' % search
        r = requests.get(url)
        soup = BeautifulSoup(r.text)
        title = soup.title.text
        content = soup.select('div > p')[0].text
        content = re.sub('\'','\\\'',re.sub('\\n','',re.sub('\[.*?\]','',content)))
        if content == 'Other reasons this message may be displayed:':
            self.privmsg(msgrecv['context'],'Wikipedia 03%s – 12No article found. Maybe you could write it: 11https://en.wikipedia.org/w/index.php?title=Special:UserLogin&returnto=%s' % (title, search))
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
            self.privmsg(msgrecv['context'],'Wikipedia 03%s – 12%s 11(%s)' % (title, exerpt, r.url))
                
class IRCbot:
    socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    
    def __init__(self):
        try:
            with open('nwobot.conf', 'r') as file:
                f = file.read()
                self.info = eval(f)
        except:
            setup()
        with open('users.txt', 'r') as file:
            f = file.read()
            self.userDict = eval(f)
        if self.info['SASL'].lower() == 'y':
            self.SASL = True
        else:
            self.SASL = False
        self.activeDict = {}
        self.allUserList = []
        for channel in self.info['CHAN'].split(','):
            self.activeDict[channel] = {}
        reddit.redditAPI(self)
        self.connect()
        self.main()
        
    def connect(self):
        self.socket.connect((self.info['HOST'], int(self.info['PORT'])))
        self.irc = ssl.wrap_socket(self.socket)
        if self.SASL:
            self.ircSend('CAP LS')
        self.ircSend('NICK %s' % self.info['NICK'])
        self.ircSend('USER %s %s %s :%s' % (self.info['NICK'], self.info['NICK'], self.info['NICK'], self.info['NAME']))
        self.ircSend('JOIN %s' % self.info['CHAN'])
        
    def main(self):
        while True:
#            try:
            serverRaw = self.irc.recv(4096).decode('utf-8')
            serverOut = str(serverRaw).split('\n')
            for line in serverOut:
                if len(line) < 1:
                    continue
                print (line)
                curTime = time.mktime(time.gmtime())
                words = str(line).split()
                prefix = ''
                nick = ''
                ident = ''
                host = ''
                trail = []
                parameters = []
                if line[0] == ':':
                    prefix = words.pop(0)[1:]
                    if '!' in prefix and '@' in prefix:
                        nick = prefix.split('!')[0]
                        ident = prefix.split('!')[1].split('@')[0]
                        host = prefix.split('@')[1]
                if len(words) > 0:
                    command = words.pop(0)
                    for i in range(len(words)):
                        if words[0][0] == ':':
                            break
                        parameters.append(words.pop(0))
                trail = ' '.join(words).split()
                if len(trail) > 0 and len(trail[0]) > 0:
                    trail[0] = trail[0][1:]
                    if len(trail[0]) > 0 and (trail[0][0] == '+' or trail[0][0] == '-'):
                        CAP = trail[0][0]
                        trail[0] = trail[0][1:]

                # SASL
                if self.SASL:
                    if command == 'CAP' and parameters [0] == '*' and parameters[1] == 'LS':
                        self.ircSend('CAP REQ :%s' % ' '.join(trail))
                        continue
                    if command == 'CAP' and parameters [1] == 'ACK':
                        self.ircSend('AUTHENTICATE PLAIN')
                        continue
                    if command == 'AUTHENTICATE' and parameters[0] == '+':
                        sasl_token = '\0'.join((self.info['NICK'], self.info['NICK'], self.info['PASS']))
                        self.ircSend('AUTHENTICATE %s' % base64.b64encode(sasl_token.encode('utf-8')).decode('utf-8'))
                        continue
                    if command == '903':
                        self.ircSend('CAP END')
                        self.ircSend('JOIN %s' % self.info['CHAN'])
                        continue

                # reply to pings
                if command == 'PING':
                    self.ircSend('PONG :%s' % trail[0])
                    continue

                # checks when identified with nickserv
                if command == 'NOTICE' and nick == 'NickServ':
                    if len(trail) > 3:
                        if 'registered' in trail[3]:
                            self.ircSend('PRIVMSG NickServ :identify %s' % self.info['PASS'])
                            continue
                        if trail[3] == 'identified':
                            self.ircSend('JOIN %s' % self.info['CHAN'])
                            continue

                # checks for INVITE received
                if command == 'INVITE' and parameters[0] == self.info['NICK']:
                    if trail[0] not in self.info['CHAN'].split(','):
                        self.info['CHAN'] = str(self.info['CHAN'])+','+trail[0]
                        self.updateFile()
                        self.ircSend('JOIN %s' % self.info['CHAN'])

                # checks nick change
                if command == 'NICK':
                    if nick == self.info['NICK']:
                        self.info['NICK'] = trail[0]
                    else:
                        self.ircSend('WHOIS %s' % trail[0])
                    continue

                # parses WHOIS result
                if str(command) == '330' and len(parameters) > 2:
                    if parameters[2] not in self.userDict:
                        self.userDict[parameters[2]] = []
                    if parameters[1] not in self.userDict[parameters[2]]:
                        self.userDict[parameters[2]].append(parameters[1])
                    self.updateFile()
                    continue

                # updates active list if user leaves
                if command == 'PART':
                    if nick in self.activeDict[parameters[0]]:
                        del self.activeDict[parameters[0]][nick]
                    continue
                if command == 'QUIT':
                    for channels in self.info['CHAN'].split(','):
                        if nick in self.activeDict[channels]:
                            del self.activeDict[channels][nick]
                    continue

                # checks when PRIVMSG received
                if command == 'PRIVMSG':
                    msgrecv = {}
                    msgrecv['context']=parameters[0]
                    msgrecv['nick']=nick
                    msgrecv['ident']=ident
                    msgrecv['host']=host
                    msgrecv['trail']=trail
                    msgrecv['line']=line
                    
                    def commandValid(cmd,minwords=1):
                        if len(trail) >= minwords and cmd in trail[0].lower() and len(trail[0]) <= len(cmd) + 1:
                            return True
                        else:
                            return False

                    # gets the current context
                    context = parameters[0]

                    # builds last spoke list
                    if context not in self.activeDict and context:
                        self.activeDict[context] = {}
                    self.activeDict[context][nick] = curTime
                    validList = []
                    for unicks in self.userDict.values():
                        validList.extend(unicks)
                    if nick not in validList and CAP == '+':
                        self.ircSend('WHOIS %s' % nick)

                    # returns active users
                    if commandValid('!active'):
                        if len(self.listActive(context)) == 1:
                            self.privmsg(context,'There is 1 active user here (only users identified with NickServ are included)')
                        else:
                            self.privmsg(context,'There are %s active users in here (only users identified with NickServ are included)')

                    # list modifier commands
                    if len(trail) > 2 and (trail[1].lower() == 'add' or trail[1].lower() == 'remove'):
                        def addRemoveList(issuer,issuerNick,command,additem,addcat):
                            if issuer in self.info['SUDOER'].split(',') or issuer in self.info['OWNER'].split(','):
                                if command == 'add':
                                    for item in additem:
                                        if item not in self.info[addcat]:
                                            self.info[addcat] = self.info[addcat]+','+item
                                elif command == 'remove':
                                    for item in additem:
                                        if item in self.info[addcat].split(','):
                                            updatedList = self.info[addcat].split(',')
                                            updatedList.remove(item)
                                            self.info[addcat] = ','.join(updatedList)
                                self.updateFile()
                            else:
                                self.privmsg(context,'NOTICE %s :You are not authorized to perform that command' % issuerNick)

                        # adds channels to autojoin list and joins them
                        if commandValid('!channel',3):
                            addRemoveList(host,nick,trail[1].lower(),trail[2:],'CHAN')
                            self.ircSend('JOIN %s' % self.info['CHAN'])
                            if trail[1].lower() == 'remove':
                                self.ircSend('PART %s' % ','.join(trail[2:]))
                            continue

                        # adds users to ignore list (ie: bots)
                        if commandValid('!ignore',3):
                            addRemoveList(host,nick,trail[1].lower(),trail[2:],'IGNORE')
                            continue

                        # adds users to sudoer list (ie: admins)
                        if commandValid('!admin',3):
                            addRemoveList(host,nick,trail[1].lower(),trail[2:],'SUDOER')
                            continue

                    # executes command
                    if commandValid('!nwodo',3):
                        if host in self.info['SUDOER'].split(',') or host in self.info['OWNER'].split(','):
                            self.ircSend(' '.join(trail[1:]))
                        continue

                    # soaker!
                    if nick == 'Doger' and len(trail) > 6:
                        if trail[0] == 'Such' and trail[6].strip('!') == self.info['NICK']:
                            initAmount = int(trail[4][1:])
                            activeUser = self.listActive(context,10,trail[1])
                            if len(activeUser) > 0:
                                tipAmount = initAmount // len(activeUser)
                                if tipAmount >= 10:
                                    self.privmsg('Doger','mtip %s %s' % ((' %s ' % str(tipAmount)).join(activeUser),str(tipAmount)))
                                    self.privmsg(context,'%s is tipping %s shibes with Ɖ%s: %s' % (trail[1], len(activeUser), tipAmount, ', '.join(activeUser)))
                                else:
                                    self.privmsg('Doger','mtip %s %s' % (trail[1], initAmount))
                                    self.privmsg(context,'Sorry %s, not enough to go around. Returning tip.' % trail[1])
                            else:
                                self.privmsg('Doger','mtip %s %s' % (trail[1], initAmount))
                                self.privmsg(context,'Sorry %s, nobody is active! Returning tip.' % trail[1])
                        continue

                    # checks for reddit command
                    if commandValid('!reddit',2):
                        reddit.command(self,msgrecv)
                        continue

                    # Urban Dictionary definitions
                    if commandValid('!ud',2):
                        ud.command(self,msgrecv)
                        continue

                    # Google search
                    if commandValid('!google',2):
                        google.command(self,msgrecv)
                        continue

                    # allows people to search for wikipedia articles
                    if commandValid('!wiki',2):
                        google.command(self,msgrecv)
                        continue

                    # fetches Youtube video info
                    if 'youtu.be' in line or 'youtube.com' in line:
                        for w in trail:
                            if 'youtu.be/' in w:
                                vidID = w.split('youtu.be/')[1]
                                break
                            elif 'youtube.com/watch?v=' in w:
                                vidID = w.split('youtube.com/watch?v=')[1]
                                break
                            elif 'youtube.com/v/' in w:
                                vidID = w.split('youtube.com/v/')[1]
                                break
                        vidID = vidID.split('#')[0].split('&')[0].split('?')[0]
                        payload = {'part': 'snippet,statistics', 'id': vidID, 'key': self.info['YTAPI']}
                        r = requests.get('https://www.googleapis.com/youtube/v3/videos', params = payload)
                        data = r.json()
                        title = data['items'][0]['snippet']['title']
                        channel = data['items'][0]['snippet']['channelTitle']
                        likes = int(data['items'][0]['statistics']['likeCount'])
                        dislikes = int(data['items'][0]['statistics']['dislikeCount'])
                        votes = likes + dislikes
                        if likes and dislikes:
                            bar = '12' + str(likes) + ' ' + '—' * round(likes*10/votes) + '15' + '—' * round(dislikes*10/votes) + ' ' + str(dislikes)
                        else:
                            bar = ''
                        self.privmsg(context,'You00,04Tube %s 14uploaded by %s – %s' % (title, channel, bar))
                        continue
                        
                    # gets basic massdrop information and also fixes link to include guest_open
                    if 'https://www.massdrop.com/' in line:
                        for w in trail:
                            if 'https://www.massdrop.com/' in w:
                                url = w
                                if not '?mode=guest_open' in line:
                                    url = url + '?mode=guest_open'
                        try:
                            r = requests.get(url)
                            soup = BeautifulSoup(r.text)
                            title = soup.title.text
                            cprice = soup.find(class_="current-price")
                            mrsp = cprice.next_sibling.next_sibling.next_sibling.next_sibling
                            tRem = soup.find(class_="item-time").text
                            self.privmsg(context,'Massdrop 02%s – 03Price: %s – 10MRSP: %s – 07%s 12(%s)' % (title, cprice.text, mrsp.text[5:], tRem, url))
                        except Exception as e:
                            print(e)
                        continue
                        
                    # general link getting
                    if 'http://' in line or 'https://' in line:
                        for w in trail:
                            if 'http://' in w or 'https://' in w:
                                url = w
                                break
                        try:
                            r = requests.get(url, timeout=2)
                            soup = BeautifulSoup(r.text)
                            title = soup.title.text
                            if title:
                                self.privmsg(context,'03%s 09(%s)' % (title, url))
                        except Exception as e:
                            print(e)
                        continue
#            except Exception as e:
#                print(e)
        
    def updateFile(self):
        with open('nwobot.conf', 'w+') as file:
            file.write(str(self.info))
        with open('users.txt', 'w+') as file:
            file.write(str(self.userDict))
    
    def listActive(self,chan,minutes=10,caller=None):
        activeList = []
        validList = []
        curTime = time.mktime(time.gmtime())
        userDict = list(self.userDict)
        mostRecent = list(dict(sorted(self.activeDict[chan].items(), key=itemgetter(1), reverse=True)).keys())
        for group in userDict:
            nickList = self.userDict[group]
            if caller != None and caller in nickList:
                userDict.remove(group)
                break
        for rnick in mostRecent:
            for group in userDict:
                nickList = self.userDict[group]
                for unick in nickList:
                    if rnick == unick:
                        validList.append(rnick)
                        userDict.remove(group)
                        break
        for key in validList:
            if key not in self.info['IGNORE'] and curTime - self.activeDict[chan][key] <= minutes * 60:
                activeList.append(key)
        return activeList
    
    def curTime(self):
        ctime = time.mktime(time.gmtime())
        return ctime
                        
    def privmsg(self,con,msg):
        self.ircSend('PRIVMSG %s :%s' % (con,msg))

    def ircSend(self,msg):
        print(msg)
        self.irc.send(bytes(str(msg)+'\r\n', 'UTF-8'))
IRCbot()