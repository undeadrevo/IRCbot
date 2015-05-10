#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lxml import etree
from operator import itemgetter
import base64, praw, re, requests, socket, ssl, time

# Author = Brian W.

class setupBot:
    def __init__(self):
        yesorno = input("Do you want to write a new configuration file? y/N: ")
        if 'Y' in yesorno or 'y' in yesorno:
            while True:
                self.newinfo = {}
                self.newinfo['HOST'] = input("\nEnter the IRC network that the bot should join: ")
                self.newinfo['PORT'] = input("Enter the port that the bot should connect with: ")
                self.newinfo['NICK'] = input("Enter the nickname that the bot should use: ")
                self.newinfo['SASL'] = input("Do you to authenticate using SASL? (y/N): ")
                self.newinfo['PASS'] = input("Enter the password that the bot will authenticate with (if applicable): ")
                self.newinfo['NAME'] = input("Enter the realname that the bot should have: ")
                self.newinfo['CHAN'] = input("Enter the channels that the bot should join (comma separated): ")
                self.newinfo['IGNORE'] = input("Enter the nicks that the bot should ignore (comma separated): ")
                self.newinfo['OWNER'] = input("Enter the hosts of the owner(s) (comma separated): ")
                self.newinfo['SUDOER'] = input("Enter the hosts to receive extra privileges (comma separated): ")
                self.newinfo['YTAPI'] = input("Enter your YouTube Google API key: ")
                print("\n%s" % self.newinfo)
                confirm = input("\n Confirm? y/N: ")
                if 'Y' in confirm or 'y' in confirm:
                    break
            with open('nwobot.conf', 'w+') as file:
                file.write(str(self.newinfo))
            with open('users.txt', 'w+') as file:
                self.userlist = {}
                file.write(str(self.userlist))

class IRCbot:
    # Reddit API
    r = praw.Reddit('redFetch by u/NewellWorldOrder''Fetches reddit submission links')
    enableNSFW = r.get_random_subreddit(nsfw=True)
    
    # Reddit API limiter
    redditLimit = time.mktime(time.gmtime())
    
    socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    def __init__(self):
        with open('nwobot.conf', 'r') as file:
            f = file.read()
            self.info = eval(f)
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
        self.connect()
        
    def connect(self):
        self.socket.connect((self.info['HOST'], int(self.info['PORT'])))
        self.irc = ssl.wrap_socket(self.socket)
        self.ircSend('CAP LS')
        self.ircSend('NICK %s' % self.info['NICK'])
        self.ircSend('USER %s %s %s :%s' % (self.info['NICK'], self.info['NICK'], self.info['NICK'], self.info['NAME']))
        self.main()
        
    def joinChannel(self):
        self.ircSend('JOIN %s' % self.info['CHAN'])

    def main(self):
        while True:
            try:
                buffr = self.irc.recv(4096).decode('utf-8')
                lines = str(buffr).split('\n')
                for line in lines:
                    if len(line) < 1:
                        continue
                    print (line)
                    curTime = time.mktime(time.gmtime())
                    words = str(line).split()
                    prefix = ''
                    trail = []
                    parameters = []
                    if line[0] == ':':
                        prefix = words.pop(0)[1:]
                    if len(words) > 0:
                        command = words.pop(0)
                    for i in range(len(words)):
                        if words[0][0] == ':':
                            break
                        parameters.append(words.pop(0))
                    trail = ' '.join(words)[1:].lstrip('+-').split()
                    Nick = ''
                    Ident = ''
                    Host = ''
                    if '!' in prefix and '@' in prefix:
                        Nick = prefix.split('!')[0]
                        Ident = prefix.split('!')[1].split('@')[0]
                        Host = prefix.split('@')[1]
                    
                    # SASL
                    if self.SASL:
                        if command == 'CAP' and parameters [0] == '*' and parameters[1] == 'LS':
                            self.ircSend('CAP REQ :%s' % ' '.join(trail))
                        if command == 'CAP' and parameters [1] == 'ACK':
                            self.ircSend('AUTHENTICATE PLAIN')
                        if command == 'AUTHENTICATE' and parameters[0] == '+':
                            sasl_token = '\0'.join((self.info['NICK'], self.info['NICK'], self.info['PASS']))
                            self.ircSend('AUTHENTICATE %s' % base64.b64encode(sasl_token.encode('utf-8')).decode('utf-8'))
                        if command == '903':
                            self.ircSend('CAP END')
                            self.joinChannel()
                        
                    # reply to pings
                    if command == 'PING':
                        self.ircSend('PONG :%s' % trail[0])

                    # checks when identified with nickserv
                    if command == 'NOTICE' and Nick == 'NickServ':
                        if len(trail) > 3:
                            if 'registered' in trail[3]:
                                self.ircSend('PRIVMSG NickServ :identify %s' % self.info['PASS'])
                            if trail[3] == 'identified':
                                self.joinChannel()

                    # checks for INVITE received
                    if command == 'INVITE' and parameters[0] == self.info['NICK']:
                        self.addChannel(trail[0])

                    # checks nick change
                    if command == 'NICK':
                        if Nick == self.info['NICK']:
                            self.info['NICK'] = trail[0]
                        else:
                            self.ircSend('WHOIS %s' % Nick)

                    # parses WHOIS result
                    if str(command) == '330' and len(parameters) > 2:
                        if parameters[2] not in self.userDict:
                            self.userDict[parameters[2]] = []
                        if parameters[1] not in self.userDict[parameters[2]]:
                            self.userDict[parameters[2]].append(parameters[1])
                        self.updateFile()

                    # updates active list if user leaves
                    if command == 'PART':
                        if Nick in self.activeDict[parameters[0]]:
                            del self.activeDict[parameters[0]][Nick]
                    if command == 'QUIT':
                        for channels in self.info['CHAN'].split(','):
                            if Nick in self.activeDict[channels]:
                                del self.activeDict[channels][Nick]

                    # checks when PRIVMSG received
                    if command == 'PRIVMSG':
                            
                        # gets the current channel
                        context = parameters [0]

                        # builds last spoke list
                        if context not in self.activeDict:
                            self.activeDict[context] = {}
                        self.activeDict[context][Nick] = curTime
                        validList = []
                        for unicks in self.userDict.values():
                            validList.extend(unicks)
                        if Nick not in validList and Nick not in self.allUserList:
                            self.ircSend('WHOIS %s' % Nick)
                            self.allUserList.append(Nick)

                        # returns active users
                        if trail[0].lower() == '!active':
                            if len(self.listActive(context)) == 1:
                                self.ircSend('PRIVMSG %s :There is 1 active user here (only users identified with NickServ are included)' % context)
                            else:
                                self.ircSend('PRIVMSG %s :There are %s active users in here (only users identified with NickServ are included)' % (context, len(self.listActive(context))))

                        # adds channels to autojoin list and joins them
                        elif '!channel' in trail[0].lower() and len(trail) > 2 and len(trail[0]) <= 9:
                            self.addRemoveList(Host,trail[1].lower(),trail[2:],'CHAN')
                            self.joinChannel()

                        # adds users to ignore list (ie: bots)
                        elif '!ignore' in trail[0].lower() and len(trail) > 2 and len(trail[0]) <= 8:
                            self.addRemoveList(Host,trail[1].lower(),trail[2:],'IGNORE')

                        # adds users to sudoer list (ie: admins)
                        elif '!admin' in trail[0].lower() and len(trail) > 2 and len(trail[0]) <= 7:
                            self.addRemoveList(Host,trail[1].lower(),trail[2:],'SUDOER')

                        # executes command
                        elif '!nwodo' in trail[0].lower() and len(trail) > 2 and len(trail[0]) <= 7:
                            if Host in self.info['SUDOER'].split(',') or Host in self.info['OWNER'].split(','):
                                self.ircSend(' '.join(trail[1:]))
                                
                        # soaker!
                        if Nick == 'Doger' and len(trail) > 6:
                            if trail[0] == 'Such' and trail[6].strip('!') == self.info['NICK']:
                                initAmount = int(trail[4][1:])
                                activeUser = self.listActive(context,10,trail[1])
                                if len(activeUser) > 0:
                                    tipAmount = initAmount // len(activeUser)
                                    if tipAmount >= 10:
                                        self.ircSend('PRIVMSG Doger :mtip %s %s' % ((' %s ' % str(tipAmount)).join(activeUser),str(tipAmount)))
                                        self.ircSend('PRIVMSG %s :%s is tipping %s shibes with Ɖ%s: %s' % (context, trail[1], len(activeUser), tipAmount, ', '.join(activeUser)))
                                    else:
                                        self.ircSend('PRIVMSG Doger :mtip %s %s' % (trail[1], initAmount))
                                        self.ircSend('PRIVMSG %s :Sorry %s, not enough to go around. Returning tip.' % (context, trail[1]))
                                else:
                                    self.ircSend('PRIVMSG Doger :mtip %s %s' % (trail[1], initAmount))
                                    self.ircSend('PRIVMSG %s :Sorry %s, nobody is active! Returning tip.' % (context,trail[1]))

                        # checks for reddit command
                        if '!reddit' in trail[0].lower() and len(trail) > 1 and len(trail[0]) <= 8:
                            if curTime - IRCbot.redditLimit > 2:
                                try:
                                    subreddit = trail[1]
                                    submission = IRCbot.r.get_subreddit(subreddit).get_random_submission()
                                    if submission.over_18:
                                        nsfwstatus = '[NSFW]'
                                    else:
                                        nsfwstatus = ''
                                    self.ircSend('PRIVMSG %s :07,00Reddit 04%s10[r/%s] 12%s - 14%s' % (context, nsfwstatus, subreddit, submission.title, submission.url))
                                except:
                                    pass
                                IRCbot.redditLimit = time.mktime(time.gmtime())
                            else:
                                self.ircSend('NOTICE %s :Please wait %s second(s) (reddit API restrictions)' % (Nick, str(2 - (curTime - IRCbot.redditLimit))))

                        # checks for urban dictionary command
                        elif '!ud' in trail[0].lower() and len(trail) > 1 and len(trail[0]) <= 4:
                            try:
                                r = requests.get('http://api.urbandictionary.com/v0/define?term=%s' % '+'.join(trail[1:]))
                                data = r.json()
                                definition = ' '.join(data['list'][0]['definition'].splitlines())
                                truncated = ''
                                if len(definition) >= 150:
                                    truncated = '...'
                                    definition = definition[:146]
                                self.ircSend('PRIVMSG %s :08,07Urban Dictionary 12[%s] 06%s%s - 10%s' % (context, data['list'][0]['word'], definition[:149], truncated, data['list'][0]['permalink']))
                            except Exception as e:
                                print(e)
                        elif '!google' in trail[0].lower() and len(trail) > 1 and len(trail[0]) <= 8:
                            r = requests.get('https://www.google.com/search?q=%s&btnI' % '+'.join(trail[1:]))
                            if r.url == 'https://www.google.com/search?q=%s&btnI' % '+'.join(trail[1:]):
                                self.ircSend('PRIVMSG %s :12G04o08o12g03l04e 06[%s] 13%s' % (context,' '.join(trail[1:]), r.url[:-5]))
                            else:
                                self.ircSend('PRIVMSG %s :12G04o08o12g03l04e 06[%s] 13%s' % (context,' '.join(trail[1:]), r.url))
                        elif '!wiki' in trail[0].lower() and len(trail) > 1 and len(trail[0]) <= 6:
                            url = 'http://en.wikipedia.org/wiki/%s' % '_'.join(trail[1:])
                            r = requests.get(url)
                            tree = etree.HTML(r.text)
                            title = ''.join(tree.xpath('/html/body/div[@id="content"]/h1[@id="firstHeading"]//text()'))
                            content = ''.join(tree.xpath('/html/body/div[@id="content"]/div[@id="bodyContent"]/div[@id="mw-content-text"]/p[1]//text()'))
                            content = re.sub('\[.*?\]','',content)
                            exerpt = '. '.join(content.split('. ')[:2])
                            if exerpt[-1] != '.':
                                exerpt = exerpt + '.'
                            self.ircSend('PRIVMSG %s :Wikipedia 03[%s] 12%s 11%s' % (context, title, exerpt, url))
                            
                        
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
                            try:
                                payload = {'part': 'snippet,statistics', 'id': vidID, 'key': self.info['YTAPI']}
                                r = requests.get('https://www.googleapis.com/youtube/v3/videos', params = payload)
                                data = r.json()
                                likes = int(data['items'][0]['statistics']['likeCount'])
                                dislikes = int(data['items'][0]['statistics']['dislikeCount'])
                                votes = likes + dislikes
                                if likes and dislikes:
                                    bar = '12' + str(likes) + ' ' + '—' * round(likes*10/votes) + '15' + '—' * round(dislikes*10/votes) + ' ' + str(dislikes)
                                else:
                                    bar = ''
                                ytInfo = '%s 14uploaded by %s  %s' % (data['items'][0]['snippet']['title'], data['items'][0]['snippet']['channelTitle'], bar)
                                self.ircSend('PRIVMSG %s :01,00You00,04Tube %s' % (context, ytInfo))
                            except Exception as e:
                                print(e)
                        elif 'http://' in line or 'https://' in line:
                            for w in trail:
                                if 'http://' in w:
                                    url = w
                                    break
                                if 'https://' in w:
                                    url = w
                                    break
                            try:
                                r = requests.get(url, timeout=2)
                                tree = etree.HTML(r.text)
                                title = tree.xpath('/html/head/title/text()')[0].strip()
                                if title:
                                    self.ircSend('PRIVMSG %s :09[%s] 03%s' % (context, url, title))
                            except Exception as e:
                                print(e)
                                
            except Exception as e:
                print(e)
                
    def addRemoveList(self,issuer,command,additem,addcat):
        if issuer in self.info['SUDOER'].split(',') or issuer in self.info['OWNER'].split(','):
            if command == 'add':
                for item in additem:
                    if item not in self.info[addcat]:
                        self.info[addcat] = self.info[addcat]+','+item
            elif command == 'remove':
                for item in additem:
                    if user in self.info[addcat].split(','):
                        updatedList = self.info[addcat].split(',')
                        updatedList.remove(item)
                        self.info[addcat] = ','.join(updatedList)
            self.updateFile()
    
    def addChannel(self,channel):
        if channel not in self.info['CHAN'].split(','):
            self.info['CHAN'] = str(self.info['CHAN'])+','+channel
        self.updateFile()
        self.joinChannel()
        
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

    def ircSend(self,msg):
        print(msg)
        self.irc.send(bytes(str(msg)+'\r\n', 'UTF-8'))

#setupBot()
IRCbot()
