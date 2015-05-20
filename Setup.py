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