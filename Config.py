# coding=utf8

def config(self):
    try:
        with open('nwobot.conf', 'r') as file:
            self.info = eval(file.read())
    except:
        setup()
        config(self)
    try:
        with open('users', 'r') as file:
            self.userDict = eval(file.read())
    except:
        userlist()
<<<<<<< HEAD
        config(self)
    if self.info['SASL'].lower() == 'y':
        self.SASL = True
    else:
        self.SASL = False
=======
        config()
>>>>>>> origin/master

def setup():
    unconfirmed = True
    while unconfirmed:
        conf = {}
        conf['HOST'] = input("\nEnter the IRC network that the bot should join: ")
        conf['PORT'] = input("Enter the port that the bot should connect with: ")
        conf['NICK'] = input("Enter the nickname that the bot should use: ")
        saslInput = input("Do you to authenticate using SASL? (y/N): ")
        if 'y' in saslInput.lower():
            conf['SASL'] = True
        else:
            conf['SASL'] = False
        conf['PASS'] = input("Enter the password that the bot will authenticate with (if applicable): ")
        conf['NAME'] = input("Enter the realname that the bot should have: ")
        conf['CHAN'] = input("Enter the channels that the bot should join (comma separated): ").split(',')
        conf['IGNORE'] = input("Enter the nicks that the bot should ignore (comma separated): ").split(',')
        conf['OWNER'] = input("Enter the hosts of the owner(s) (comma separated): ").split(',')
        conf['SUDOER'] = input("Enter the hosts to receive extra privileges (comma separated): ").split(',')
        confirm = input("\n Confirm? y/N: ")
        if 'y' in confirm.lower():
            unconfirmed = False
    with open('nwobot.conf', 'w+') as file:
        file.write(str(conf))

def userlist():
    with open('users', 'w+') as file:
        userlist = {}
        file.write(str(userlist))
