#!/usr/bin/env python
# -*- coding: utf-8 -*-

import praw, socket, ssl, time

__author__ = 'Brian W.'

class setupBot:
    def __init__(self):
        yesorno = input("Do you want to write a new configuration file? y/N: ")
        if 'Y' in yesorno or 'y' in yesorno:
            while True:
                self.newinfo = {}
                self.newinfo['HOST'] = input("\nEnter the IRC server that the bot should join: ")
                self.newinfo['PORT'] = input("Enter the port that the bot should connect with: ")
                self.newinfo['NICK'] = input("Enter the nickname that the bot should use: ")
                self.newinfo['PASS'] = input("Enter the password that the bot will authenticate with (if applicable): ")
                self.newinfo['NAME'] = input("Enter the realname that the bot should have: ")
                self.newinfo['CHAN'] = input("Enter the channels that the bot should join (comma separated): ")
                self.newinfo['IGNORE'] = input("Enter the nicks that the bot should ignore (comma separated): ")
                self.newinfo['OWNER'] = input("Enter the hosts of the owner(s) (comma separated): ")
                self.newinfo['SUDOER'] = input("Enter the hosts to receive extra privileges (comma separated): ")
                self.newinfo['USERNAMES'] = {}
                print("\n%s" % self.newinfo)
                confirm = input("\n Confirm? y/N: ")
                if 'Y' in confirm or 'y' in confirm:
                    break
            with open('nwobot.conf', 'w+') as file:
                file.write(str(self.newinfo))

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
        self.activeDict = {}
        for channel in self.info['CHAN'].split(','):
            self.activeDict[channel] = {}
        self.connect()
        
    def connect(self):
        self.socket.connect((self.info['HOST'], int(self.info['PORT'])))
        self.irc = ssl.wrap_socket(self.socket)
        self.ircSend('NICK %s' % self.info['NICK'])
        self.ircSend('USER %s %s %s :%s' % (self.info['NICK'], self.info['NICK'], self.info['NICK'], self.info['NAME']))
        self.main()
        
    def joinChannel(self):
        self.ircSend('JOIN %s' % self.info['CHAN'])

    def main(self):
        while True:
            try:
                buffr = self.irc.recv(4096).decode('UTF-8')
                lines = str(buffr).split('\n')
                for line in lines:
                    if len(line) < 1:
                        continue
                    print (line)
                    words = str(line).split()
                    trail = []
                    parameters = []
                    if line[0] == ':':
                        prefix = words.pop(0)[1:]
                    else:
                        prefix = ''
                    command = words.pop(0)
                    for i in range(len(words)):
                        if words[0][0] == ':':
                            break
                        parameters.append(words.pop(0))
                    trail = ' '.join(words)[1:].split()
                    
                    if '!' in prefix and '@' in prefix:
                        Nick = prefix.split('!')[0]
                        Ident = prefix.split('!')[1].split('@')[0]
                        Host = prefix.split('@')[1]
                    else:
                        Nick = ''
                        Ident = ''
                        Host = ''

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

                    # adds users to username list
                    if command == 'JOIN':
                        if Nick == self.info['NICK']:
                            self.ircSend('WHO {0} %an'.format(parameters[0]))
                        else:
                            self.ircSend('WHOIS %s' % Nick)
                    
                    # parses WHO(IS) command
                    if str(command) == '354' or str(command) == '330':
                        if parameters[2] not in self.info['USERNAMES']:
                            self.info['USERNAMES'][parameters[2]] = []
                        if parameters[1] not in self.info['USERNAMES'][parameters[2]]:
                            self.info['USERNAMES'][parameters[2]].append(parameters[1])
                        self.updateFile()
                        
                    # updates active list if user leaves
                    if command == 'PART':
                        if Nick in self.activeDict[parameters[0]]:
                            self.activeDict[parameters[0]].pop(Nick, None)
                    if command == 'QUIT':
                        for channels in self.info['CHAN'].split(','):
                            if Nick in self.activeDict[channels]:
                                self.activeDict[channels].pop(Nick, None)
                        
                    # checks when PRIVMSG received
                    if command == 'PRIVMSG':
                        # gets the current channel
                        context = parameters [0]

                        # builds last spoke list
                        if context not in self.activeDict:
                            self.activeDict[context] = {}
                        self.activeDict[context][Nick] = time.mktime(time.gmtime())
                        
                        # returns active users
                        if trail[0].lower() == '!active':
                            self.ircSend('PRIVMSG %s :There are %s user(s) in here' % (context, len(self.listActive(context))))
                            
                        # adds channels to autojoin list and joins them
                        elif trail[0].lower() == '!channel' and len(trail) > 2:
                            self.addRemoveList(Host,trail[1].lower,trail[2:],'CHAN')
                            self.joinChannel()
                            
                        # adds users to ignore list (ie: bots)
                        elif trail[0].lower() == '!ignore' and len(trail) > 2:
                            self.addRemoveList(Host,trail[1].lower,trail[2:],'IGNORE')
                                
                        # adds users to sudoer list (ie: admins)
                        elif trail[0].lower() == '!admin' and len(trail) > 2:
                            self.addRemoveList(Host,trail[1].lower,trail[2:],'SUDOER')

                        # executes command
                        elif trail[0] == '!nwodo':
                            if Host in self.info['SUDOER'].split(',') or Host in self.info['OWNER'].split(','):
                                self.ircSend(' '.join(trail[1:]))

                        # checks for reddit command
                        elif trail[0] == '!reddit':
                            if time.mktime(time.gmtime()) - IRCbot.redditLimit > 2:
                                try:
                                    subreddit = trail[1]
                                    submission = IRCbot.r.get_subreddit(subreddit).get_random_submission()
                                    self.ircSend('PRIVMSG %s :%s - %s' % (context, submission.title, submission.url))
                                except:
                                    pass
                                IRCbot.redditLimit = time.mktime(time.gmtime())     
            except Exception as e:
                print(e)
                
    def addRemoveList(self,issuer,command,additem,addcat):
        if issuer in self.info['SUDOER'].split(',') or issuer in self.info['OWNER'].split(','):
            if command == 'add':
                for item in additem:
                    if item not in self.info[addcat].split(','):
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
    
    def listActive(self,chan,minutes=10):
        activeList = []
        validList = []
        for i in range(len(self.info['USERNAMES'])):
            validList.extend(list(self.info['USERNAMES'].values())[i])
        for key in self.activeDict[chan]:
            if key in validList and key not in self.info['IGNORE'] and time.mktime(time.gmtime()) - self.activeDict[chan][key] <= minutes * 60:
                activeList.append(key)
        return activeList

    def ircSend(self,msg):
        print(msg)
        self.irc.send(bytes(str(msg)+'\r\n', 'UTF-8'))

setupBot()
IRCbot()
