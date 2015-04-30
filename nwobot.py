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
                self.newinfo['SUDOER'] = input("Enter the hosts to receive extra privileges (comma separated): ")
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
            buffr = self.irc.recv(4096).decode('UTF-8')
            lines = str(buffr).split('\n')
            for line in lines:
                if len(line) < 1:
                    continue
                print (line)
                if line[0] == ':':
                    prefixEnd = line.find(' ')
                    prefix = line[1:prefixEnd]
                    if '!' in prefix and '@' in prefix:
                        Nick = prefix.split('!')[0]
                        Ident = prefix.split('!')[1].split('@')[0]
                        Host = prefix.split('!')[1].split('@')[1]
                    else:
                        Nick = ''
                        Ident = ''
                        Host = ''
                else:
                    prefixEnd = -1
                    prefix = ''
                if ' :' in line:
                    trailStart = line.find(' :')
                    trail = line[trailStart + 2:].split()
                else:
                    trailStart = -1
                    trail = []
                prefixEnd += 1
                cap = line[prefixEnd:trailStart].split()
                if len(cap) > 0:
                    command = cap[0]
                if len(cap) > 1:
                    parameters = cap[1:]
                else:
                    parameters = []

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
                    
                # checks when PRIVMSG received
                if command == 'PRIVMSG':
                    # gets the current channel
                    context = parameters [0]

                    # builds last spoke list
                    if context not in self.activeDict:
                        self.activeDict[context] = {}
                    self.activeDict[context][prefix.split('!')[0]] = time.mktime(time.gmtime())
                    
                    # returns active users
                    if trail[0] == '!active':
                        self.ircSend('PRIVMSG %s :%s' % (context, len(self.listActive(context))))
                        
                    # adds users to ignore list (ie: bots)
                    elif trail[0] == '!addignore':
                        if Host in self.info['SUDOER']:
                            self.info['IGNORE'] = self.info['IGNORE']+','+','.join(trail[1:])
                            self.updateFile()
                            
                    # adds users to sudoer list (ie: bots)
                    elif trail[0] == '!addadmin':
                        if Host in self.info['SUDOER']:
                            self.info['SUDOER'] = self.info['SUDOER']+','+','.join(trail[1:])
                            self.updateFile()

                    # executes command
                    elif trail[0] == '!nwodo':
                        if Host in self.info['SUDOER']:
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
    
    def addChannel(self,channel):
        self.info['CHAN'] = str(self.info['CHAN'])+','+channel
        self.updateFile()
        self.joinChannel()
        
    def updateFile(self):
        with open('nwobot.conf', 'w+') as file:
            file.write(str(self.info))
    
    def listActive(self,chan,minutes=10):
        activeList = []
        for key in self.activeDict[chan]:
            if key not in self.info['IGNORE'] and time.mktime(time.gmtime()) - self.activeDict[chan][key] <= minutes * 60:
                activeList.append(key)
        return activeList

    def ircSend(self,msg):
        print(msg)
        self.irc.send(bytes(str(msg)+'\r\n', 'UTF-8'))

setupBot()
IRCbot()
