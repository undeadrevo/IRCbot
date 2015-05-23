# coding=utf8

import time

def interpret(line):
    Log = {}
    Log['line'] = line
    Log['time'] = time.time()
    Log['nick'] = ''
    Log['ident'] = ''
    Log['host'] = ''
    Log['command'] = ''
    Log['parameters'] = []
    Log['cap'] = ''
    Log['trail'] = []
    words = str(line).split()
    if line[0] == ':':
        prefix = words.pop(0)[1:]
        if '!' in prefix and '@' in prefix:
            Log['nick'] = prefix.split('!')[0]
            Log['ident'] = prefix.split('!')[1].split('@')[0]
            Log['host'] = prefix.split('@')[1]
    if len(words) > 0:
        Log['command'] = words.pop(0)
        for i in range(len(words)):
            if words[0][0] == ':':
                break
            Log['parameters'].append(words.pop(0))
            
    Log['trail'] = ' '.join(words).split()
    if len(Log['trail']) > 0 and len(Log['trail'][0]) > 0:
        Log['trail'][0] = Log['trail'][0][1:]
        if len(Log['trail'][0]) > 0 and (Log['trail'][0][0] == '+' or Log['trail'][0][0] == '-'):
            Log['cap'] = Log['trail'][0][0]
            Log['trail'][0] = Log['trail'][0][1:]
            
    print('%s %s' % (time.strftime('%H:%M:%S', time.gmtime(Log['time'])), Log['line']))
    return Log