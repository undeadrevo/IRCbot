# coding=utf8

from bs4 import BeautifulSoup
from operator import itemgetter
import base64, Commands, Config, Logger, praw, re, requests, Soaker, socket, ssl, time, URLInfo

class IRC:
    def __init__(self):
        Config.config(self)
        self.activeDict = {}
        for channel in self.info['CHAN'].split(','):
            self.activeDict[channel] = {}
        Commands.redditAPI(self)
        Soaker.Soaker(self)
        self.Connect()
        self.Main()
        
    def Connect(self):
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.connect((self.info['HOST'], int(self.info['PORT'])))
        self.irc = ssl.wrap_socket(sock)
        connectMSG = []
        if self.SASL:
            connectMSG.append('CAP LS')
        connectMSG.append('NICK %s' % self.info['NICK'])
        connectMSG.append('USER %s %s %s :%s' % (self.info['NICK'], self.info['NICK'], self.info['NICK'], self.info['NAME']))
        connectMSG.append('JOIN %s' % self.info['CHAN'])
        self.irc.send(bytes('\r\n'.join(connectMSG)+'\r\n', 'UTF-8'))
        
    def Main(self):
        while True:
            serverRaw = self.irc.recv(4096).decode('utf-8')
            serverOut = str(serverRaw).split('\n')
            for line in serverOut:
                if len(line) < 1:
                    continue
                
                Log = Logger.interpret(line)
                
                # reply to pings
                if Log['command'] == 'PING':
                    self.ircSend('PONG :%s' % Log['trail'][0])
                    continue

                # SASL
                if self.SASL:
                    if Log['command'] == 'CAP':
                        if Log['parameters'] [0] == '*' and Log['parameters'][1] == 'LS':
                            self.ircSend('CAP REQ :%s' % ' '.join(Log['trail']))
                            continue
                        if Log['parameters'] [1] == 'ACK':
                            self.ircSend('AUTHENTICATE PLAIN')
                            continue
                    if Log['command'] == 'AUTHENTICATE' and Log['parameters'][0] == '+':
                        sasl_token = '\0'.join((self.info['NICK'], self.info['NICK'], self.info['PASS']))
                        self.ircSend('AUTHENTICATE %s' % base64.b64encode(sasl_token.encode('utf-8')).decode('utf-8'))
                        continue
                    if Log['command'] == '903':
                        self.ircSend('CAP END')
                        self.ircSend('JOIN %s' % self.info['CHAN'])
                        continue

                # checks when identified with nickserv
                if Log['command'] == 'NOTICE' and Log['nick'] == 'NickServ':
                    if len(trail) > 3:
                        if 'registered' in Log['trail'][3]:
                            self.ircSend('PRIVMSG NickServ :identify %s' % self.info['PASS'])
                            continue
                        if Log['trail'][3] == 'identified':
                            self.ircSend('JOIN %s' % self.info['CHAN'])
                            continue

                # checks for INVITE received
                if Log['command'] == 'INVITE' and Log['parameters'][0] == self.info['NICK']:
                    if Log['trail'][0] not in self.info['CHAN'].split(','):
                        self.info['CHAN'] = str(self.info['CHAN'])+','+Log['trail'][0]
                        self.updateFile()
                        self.ircSend('JOIN %s' % self.info['CHAN'])
                        
                # checks channel join
                if Log['command'] == 'JOIN':
                    if Log['nick'] == self.info['NICK']:
                        self.activeDict[Log['parameters'][0]] = {}
                        self.ircSend('WHO %s %%na' % Log['parameters'][0])
                    elif Log['nick'] not in self.activeDict[Log['parameters'][0]]:
                        self.activeDict[Log['parameters'][0]][Log['nick']] = 0
                        if Log['nick'] not in list(self.userDict.values()):
                            self.ircSend('WHOIS %s' % Log['trail'][0])
                    continue

                # checks nick change
                if Log['command'] == 'NICK':
                    if Log['nick'] == self.info['NICK']:
                        self.info['NICK'] = Log['trail'][0]
                    else:
                        self.ircSend('WHOIS %s' % Log['trail'][0])
                    continue

                # parses NAMES result
                if str(Log['command']) == '353' and len(Log['parameters']) > 2:
                    if Log['parameters'][-1] not in self.activeDict:
                        self.activeDict[Log['parameters'][-1]] = {}
                    for names in Log['trail']:
                        names = names.lstrip('@+')
                        if names != self.info['NICK']:
                            self.activeDict[Log['parameters'][-1]][names] = 0
                    continue
                    
                # parses WHOIS result
                if (str(Log['command']) == '330' or str(Log['command']) == '354') and len(Log['parameters']) > 2:
                    if Log['parameters'][2] not in self.userDict:
                        self.userDict[Log['parameters'][2]] = []
                    if Log['parameters'][1] not in self.userDict[Log['parameters'][2]] and Log['parameters'][1] != self.info['NICK']:
                        self.userDict[Log['parameters'][2]].append(Log['parameters'][1])
                    self.updateFile()
                    continue

                # updates active list if user leaves
                if Log['command'] == 'PART':
                    if Log['nick'] in self.activeDict[Log['parameters'][0]]:
                        del self.activeDict[Log['parameters'][0]][Log['nick']]
                    continue
                if Log['command'] == 'QUIT':
                    for channels in self.info['CHAN'].split(','):
                        if Log['nick'] in self.activeDict[channels]:
                            del self.activeDict[channels][Log['nick']]
                    continue

                # checks when PRIVMSG received
                if Log['command'] == 'PRIVMSG':
                    Log['context'] = Log['parameters'][0]
                    
                    def commandValid(cmd,minwords=1):
                        if len(Log['trail']) >= minwords and cmd in Log['trail'][0].lower() and len(Log['trail'][0]) <= len(cmd) + 1:
                            return True
                        else:
                            return False

                    # builds last spoke list
                    if Log['context'] not in self.activeDict:
                        self.activeDict[Log['context']] = {}
                    self.activeDict[Log['context']][Log['nick']] = Log['time']
                    validList = []
                    for group in self.userDict.values():
                        validList.extend(group)
                    if Log['nick'] not in validList and CAP == '+':
                        self.ircSend('WHOIS %s' % Log['nick'])

                    # list modifier commands
                    if len(Log['trail']) > 2 and (Log['trail'][1].lower() == 'add' or Log['trail'][1].lower() == 'remove'):
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
                                self.ircSend(issuerNick,'NOTICE %s :You are not authorized to perform that command' % issuerNick)

                        # adds channels to autojoin list and joins them
                        if commandValid('!channel',3):
                            addRemoveList(Log['host'],Log['nick'],Log['trail'][1].lower(),Log['trail'][2:],'CHAN')
                            self.ircSend('JOIN %s' % self.info['CHAN'])
                            if Log['trail'][1].lower() == 'remove':
                                self.ircSend('PART %s' % ','.join(Log['trail'][2:]))
                            continue

                        # adds users to ignore list (ie: bots)
                        if commandValid('!ignore',3):
                            addRemoveList(Log['host'],Log['nick'],Log['trail'][1].lower(),Log['trail'][2:],'IGNORE')
                            continue

                        # adds users to sudoer list (ie: admins)
                        if commandValid('!admin',3):
                            addRemoveList(Log['host'],Log['nick'],Log['trail'][1].lower(),Log['trail'][2:],'SUDOER')
                            continue
                                
                    Soaker.Handler(self, Log)

                    Commands.Handler(self, Log)
                    
                    URLInfo.Handler(self, Log)
        
    def updateFile(self):
        with open('nwobot.conf', 'w+') as file:
            file.write(str(self.info))
        with open('users', 'w+') as file:
            file.write(str(self.userDict))
    
    def listActive(self,chan,minutes=10,caller=None,full=False,exclude=[]):
        activeList = []
        validList = []
        timenow = time.time()
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
            if key not in self.info['IGNORE'].split(',') and key != self.info['NICK'] and key not in exclude and (timenow - self.activeDict[chan][key] <= minutes * 60 or full):
                    activeList.append(key)
        return activeList
                        
    def PRIVMSG(self,con,msg):
        self.ircSend('PRIVMSG %s :%s' % (con,msg))

    def ircSend(self,msg):
        print(msg)
        self.irc.send(bytes(str(msg)+'\r\n', 'UTF-8'))
        
IRC()