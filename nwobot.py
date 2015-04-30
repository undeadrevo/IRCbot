import praw, socket, ssl, string, sys, time

class IRCbot:
    # Reddit API
    r = praw.Reddit('redFetch by u/NewellWorldOrder''Fetches reddit submission links')
    enableNSFW = r.get_random_subreddit(nsfw=True)
    
    # Reddit API limiter
    redditLimit = time.mktime(time.gmtime())
    
    socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    def __init__(self):
#        try:
        f = open('nwobot.conf')
        self.host = f.readline().strip()
        self.port = int(f.readline().strip())
        self.nick = f.readline().strip()
        self.nicksv = bool(f.readline().strip())
        self.ident = f.readline().strip()
        self.passwd = f.readline().strip()
        self.rname = f.readline().strip()
        self.chans = f.readline().strip().split(',')
        f.close()
        self.activeDict = {}
        for chan in self.chans:
            self.activeDict[chan] = {} 
        self.connect()
#        except IOError:
#            f = open('nwobot.conf','w+')
#            f.write('Host\nPort\nNick\nNickserv (True/False)\nIdent\nPassword\nRealname\nChannels(Comma Separated)')
#            f.close()
#            sys.exit()
        
    def connect(self):
        self.socket.connect((self.host, self.port))
        self.irc = ssl.wrap_socket(self.socket)
        self.ircSend('NICK %s' % self.nick)
        self.ircSend('USER %s %s %s :%s' % (self.nick, self.nick, self.ident, self.rname))
        self.main()
        
    def joinChannel(self):
        self.ircSend('JOIN %s' % ','.join(self.chans))

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
                if command == 'NOTICE':
                    if len(trail) > 3:
                        if 'registered' in trail[3]:
                            self.ircSend('PRIVMSG NickServ :identify %s' % self.passwd)
                        if trail[3] == 'identified':
                            self.joinChannel()
                    
                # checks for INVITE received
                if command == 'INVITE' and parameters[0] == self.nick:
                    self.addChannel(trail[0])
                    
                # checks when PRIVMSG received
                if command == 'PRIVMSG':
                    # gets the current channel
                    context = parameters [0]

                    # builds last spoke list
                    if context not in self.activeDict:
                        self.activeDict[context] = {}
                    self.activeDict[context][prefix.split('!')[0]] = time.mktime(time.gmtime())

                    if trail[0] == '!active':
                        self.ircSend('PRIVMSG %s :%s' % (context, len(self.listActive(context))))

                    # checks for reddit command
                    if trail[0] == '!reddit':
                        if time.mktime(time.gmtime()) - IRCbot.redditLimit > 2:
                            try:
                                subreddit = trail[1]
                                submission = IRCbot.r.get_subreddit(subreddit).get_random_submission()
                                self.ircSend('PRIVMSG %s :%s - %s' % (context, submission.title, submission.url))
                            except:
                                pass
                            IRCbot.redditLimit = time.mktime(time.gmtime())              
    
    def addChannel(self,channel):
        f = open('nwobot.conf','a')
        f.write(','+channel)
        f.close()
        self.chans.append(channel)
        self.joinChannel()
    
    def listActive(self,chan,minutes=10):
        activeList = []
        for key in self.activeDict[chan]:
            if time.mktime(time.gmtime()) - self.activeDict[chan][key] <= minutes * 60:
                activeList.append(key)
        return activeList

    def ircSend(self,msg):
        print(msg)
        self.irc.send(bytes(str(msg)+'\r\n', 'UTF-8'))
                
IRCbot()
