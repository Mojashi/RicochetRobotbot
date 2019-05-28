import tweepy
import time
import subprocess
import json
import copy
import random
import ProblemGenerator
import re
from PIL import Image
from datetime import datetime
from imgurpython import ImgurClient

def absolutedofunc(func,*args, **kwargs):
    while True:
        try:
            ret = func(*args, **kwargs)
            return ret
        except:
            print('tweet failed')
            time.sleep(10)
    return

def decoratename(username, userid_str, userdata):
    with open('decorate.json',encoding="utf-8_sig") as f:
        decorate = json.load(f)
        for v in decorate.values():
            if v['range'][0] <= userdata[userid_str]['rank'] and v['range'][1] >= userdata[userid_str]['rank']:
                return v['deco'].replace('%user', username)
    return username

def parsetext(text, dirdict):
    ways = text.split()

    while ways[0][0] == '@':
        ways.pop(0)
        
    waysstr = ''.join(ways)

    match = re.findall(r'[a-z0-9]', waysstr.lower())

    if len(match) % 2 == 1:
        return -1

    ret = []

    for i in range(0,len(match),2):
        if ord(match[i]) >= ord('0') and ord(match[i]) <= ord('4') and match[i + 1] in dirdict.keys():
            ret.append([int(match[i]), int(dirdict[match[i + 1]])])
        else:
            return -1

    return ret

def checkanswer(mp, robotpos, goalpos, mainrobot, ans):
    Dir = [[0,-1],[1,0],[0,1],[-1,0]]

    curpos = copy.copy(robotpos)

    for way in ans:
        num = way[0]
        d = way[1]

        while True:
            nex = [curpos[num][0] + Dir[d][0],curpos[num][1] + Dir[d][1]]
            if mp[curpos[num][0]][curpos[num][1]][d] == 1 or nex in curpos:
                break
            curpos[num] = nex

    if curpos[mainrobot] != goalpos:
        return -1

    return len(ans)

def tweetnewproblem():
    
    with open('history.json','r') as f:
        history = json.load(f)

    ProblemGenerator.ProblemGenerate('problems/' + str(len(history) + 1))
    
    stat = absolutedofunc(api.update_with_media, filename='problems/' + str(len(history) + 1) + '.png', status="Problem number:" + str(len(history) + 1))

    history[len(history) + 1] = stat.id

    with open('history.json','w') as f:
        json.dump(history, f)

    return stat.id, str(len(history))

def creategif(problemname, ans):
    Dir = [[0,-1],[1,0],[0,1],[-1,0]]
    with open('problems/'+problemname+'.json') as f:
        cdict = json.load(f)
        mp = cdict['board']
        curpos = cdict['robotpos']
        goalpos = cdict['goalpos']
        mainrobot = cdict['mainrobot']
        answer =  cdict['answer']
        imgname = cdict['img']
        if 'baseimg' not in cdict.keys():
            return None
        baseimgname = cdict['baseimg']
    fimg = Image.open(imgname)
    width = int(fimg.width / 2)
    height = int(fimg.height / 2)
    imgs = [fimg.resize((width,height))]
    

    for way in ans:
        num = int(way[0])
        d = way[1]

        fr = curpos[num]
        to = curpos[num]
        while True:
            nex = [to[0] + Dir[d][0], to[1] + Dir[d][1]]
            if mp[to[0]][to[1]][d] == 1 or nex in curpos:
                break
            to = nex

        while [int(fr[0] * 10),int(fr[1] * 10)] != [int(to[0] * 10),int(to[1] * 10)]:
            nex = [fr[0] + Dir[d][0] / 1.0, fr[1] + Dir[d][1] / 1.0]
            fr = nex
            curpos[num] = fr
            imgs.append(ProblemGenerator.GenerateImage(mp,goalpos,curpos, mainrobot, baseimgname)[1].resize((width,height)))
            
        imgs.append(ProblemGenerator.GenerateImage(mp,goalpos,curpos, mainrobot, baseimgname)[1].resize((width,height)))
        imgs.append(ProblemGenerator.GenerateImage(mp,goalpos,curpos, mainrobot, baseimgname)[1].resize((width,height)))
    
        curpos[num] = [int(curpos[num][0]),int(curpos[num][1])]

    imgs[0].save('buf.gif',save_all = True, append_images=imgs[1:], optimize=True,duration=70, loop = 0)
    try:
        client = ImgurClient('756d458eceab39c', '0495cbf4706ec27591a48193c08fff6b630e9634')
        return client.upload_from_path('buf.gif')
    except:
        print("gif upload except")
        return None
    return None

def tweethourlyranking(userdata, fr, basetext="", reply_id=None):
    text = basetext + "Round Ranking:\n"
    
    sorteduser = sorted(userdata.items(), key=lambda x:sum(int(gm) >= fr for gm in x[1]['winhistory']),reverse=True)
    realrank = 1
    buf = -1
    cou = 0
    for i in range(len(sorteduser)):
        usr = userdata[sorteduser[i][0]]
        if sum(int(gm) >= fr for gm in usr['history']) == 0:
            continue

        winc = sum(int(gm) >= fr for gm in usr['winhistory'])
        if winc != buf:
            realrank = cou + 1
        text += str(realrank) + '. ' + decoratename(usr['screen_name'], sorteduser[i][0], userdata) + ' ' + str(winc) + 'win\n'
        buf = winc
        if cou == 9:
            break
        cou += 1

    if reply_id == None:
        return absolutedofunc(api.update_status, text)
    else:
        return absolutedofunc(api.update_status,text, in_reply_to_status_id = reply_id, auto_populate_reply_metadata=True)

def tweetoverallranking(userdata, basetext="", reply_id=None):
    text = "Overall Ranking:\n"
    
    sorteduser = sorted(userdata.items(), key=lambda x:x[1]['wincount'],reverse=True)
    for i in range(len(sorteduser)):
        usr = userdata[sorteduser[i][0]]
        text += str(usr['rank']) + '. ' + decoratename(usr['screen_name'], sorteduser[i][0], userdata) + ' ' + str(usr['wincount']) + 'win\n'
        if i == 9:
            break

        
    if reply_id == None:
        return absolutedofunc(api.update_status,text)
    else:
        return absolutedofunc(api.update_status,text, in_reply_to_status_id = reply_id, auto_populate_reply_metadata=True)
def setdefaultuser(userdata, usr_id_str, usr_name=''):
    userdata.setdefault(usr_id_str, {})
    userdata[usr_id_str].setdefault('rank', 9999999)
    userdata[usr_id_str].setdefault('wincount', 0)
    userdata[usr_id_str].setdefault('screen_name', usr_name)
    userdata[usr_id_str].setdefault('history', [])
    userdata[usr_id_str].setdefault('winhistory', [])
    userdata[usr_id_str].setdefault('keyconfig', {'u':0,'r':1,'d':2,'l':3})

   

def commandproc(userdata, stat, fr=-1):
    args = stat.text.split()
    while args[0][0] == '@':
        args.pop(0)

    if len(args) == 0:
        return

    if args[0] == '!myrank':
        setdefaultuser(userdata, stat.user.id_str, stat.user.screen_name)
        absolutedofunc(api.update_status,'Wins:' + str(userdata[stat.user.id_str]['wincount']) + '\nRank:' + str(userdata[stat.user.id_str]['rank']), in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
    
    elif args[0] == '!ありがとう' or args[0] == '!thank':
        absolutedofunc(api.update_status,'どういたしまして', in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
    
    elif args[0] == '!omikuji':
        kuji = ['Daikichi', 'Chukichi', 'Shokichi', 'Suekichi', 'Kyo', 'Daikyo']
        absolutedofunc(api.update_status,kuji[random.randint(0, len(kuji) - 1)], in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
    
    elif fr != -1 and args[0] == '!roundrank':
        tweethourlyranking(userdata, fr, reply_id = stat.id)

    elif args[0] == '!overallrank':
        tweetoverallranking(userdata, reply_id = stat.id)

    elif args[0] == '!janken':
            if len(args) >= 2:
                if args[1] == 'GOO' or args[1] == 'PAA' or args[1] == 'CHOKI':
                    losetext = 'YOU LOSE!'
                    wintext = 'YOU WIN!'
                    aikotext = 'YOU AIKO!'
                    wintable = {'GOO' : {'PAA':losetext, 'GOO':aikotext, 'CHOKI':wintext, 'OTHER':losetext},
                                'CHOKI' : {'PAA':wintext, 'GOO':losetext, 'CHOKI':aikotext, 'OTHER':losetext},
                                'PAA' : {'PAA':aikotext, 'GOO':wintext, 'CHOKI':losetext, 'OTHER':losetext}}
                    hands = {'✊ GOO':'GOO','👊 GOO':'GOO','🤛 GOO':'GOO','🤜 GOO':'GOO','☝ GOOCHOKI':'OTHER', '🖕 GOOCHOKI':'OTHER','✂ CHOKI':'CHOKI','✌ CHOKI':'CHOKI','🤘 CHOKI':'CHOKI','🤞 CHOKI':'CHOKI','✋ PAA':'PAA','👋 PAA':'PAA', '👐 PAA':'PAA', '🖐 PAA':'PAA','🖖 PAACHOKI':'OTHER'}
                    hand = list(hands.items())[random.randint(0,len(list(hands.keys())) - 1)]
                    absolutedofunc(api.update_status, hand[0] + '\n' + wintable[args[1]][hand[1]], in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)

    elif args[0] == '!setting':
        if len(args) <= 1:
            return
        setdefaultuser(userdata, stat.user.id_str, stat.user.screen_name)
        if args[1] == 'wasd':
            userdata[stat.user.id_str]['keyconfig'] = {'w':0,'d':1,'s':2,'a':3}
            absolutedofunc(api.create_favorite,stat.id)
    
        elif args[1] == 'urdl':
            userdata[stat.user.id_str]['keyconfig'] = {'u':0,'r':1,'d':2,'l':3}
            absolutedofunc(api.create_favorite,stat.id)
            
        elif args[1] == 'hjkl':
            userdata[stat.user.id_str]['keyconfig'] = {'k':0,'l':1,'j':2,'h':3}
            absolutedofunc(api.create_favorite,stat.id)

        with open('userdata.json', 'w') as f:
            json.dump(userdata, f)  

    elif args[0] == '!gif':
        rpd = api.get_status(stat.in_reply_to_status_id)
        gifurl = None

        with open('gifs.json','r') as f:
            algif = json.load(f)
            if rpd.id_str in algif.keys():
                gifurl = algif[rpd.id_str]

        print("gif")
        if gifurl == None:
            setdefaultuser(userdata,rpd.user.id_str, rpd.user.screen_name)
            ans = parsetext(rpd.text, userdata[rpd.user.id_str]['keyconfig'])
            if ans != -1:
                with open('history.json','r') as f:
                    history = json.load(f)
                    probnamelis = [k for k, v in history.items() if v == rpd.in_reply_to_status_id]
                    if len(probnamelis) > 0:
                        gifurl = creategif(probnamelis[0], ans)
                        algif[rpd.id_str] = gifurl

                        with open('gifs.json','w') as f:
                             json.dump(algif, f)
    
        if gifurl != None:
            absolutedofunc(api.update_status,gifurl['link'], in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)

    return

def convertans(answer, robotpos):
    Dir = {'u':[0,-1],'r':[1,0],'d':[0,1],'l':[-1,0]}
    curpos = copy.copy(robotpos)

    ret = ''
    for i in range(int(answer[0])):
        nex = answer[i + 1]
        num,y,x = [int(x) for x in nex.split(' ')]
        
        for itr in Dir.items():
            if itr[1] == [(x - curpos[num][0] > 0) - (x - curpos[num][0] < 0),(y - curpos[num][1] > 0) - (y - curpos[num][1] < 0)]:
                ret += str(num) + itr[0] + ','
                curpos[num] = [x,y]
                break

    return ret.rstrip(',')

def getmentions():

    if (datetime.now() - getmentions.lastgettime).total_seconds() >= 15:
        mentions = absolutedofunc(api.mentions_timeline,since_id=getmentions.lastid, count=199)
        for stat in mentions:
            print("from:" + stat.user.screen_name + " " + stat.text)
        getmentions.lastgettime = datetime.now()
        if len(mentions) > 0:
            getmentions.lastid = mentions[0].id
        return mentions

    return []

   

def winproc(userdata, stat, problemname):
    userdata[stat.user.id_str]['wincount']+=1
    userdata[stat.user.id_str]['winhistory'].append(problemname)

    sorteduser = sorted(userdata.items(), key=lambda x:x[1]['wincount'],reverse=True)

    realrank = 1
    buf = -1
    for i in range(len(sorteduser)):
        usr = sorteduser[i][0]
        if buf != userdata[usr]['wincount']:
            realrank = i + 1
        userdata[usr]['rank'] = realrank
        buf = userdata[usr]['wincount']

    with open('userdata.json', 'w') as f:
        json.dump(userdata, f)
    return


def maincycle(timelimit, roundstart, curproblemid, problemname):
    curshortest = 10000000
    curshorteststat = None
    
    with open('userdata.json') as f:
        userdata = json.load(f)
            
    with open('problems/' + problemname + '.json') as f:
        cdict = json.load(f)
        mp = cdict['board']
        robotpos = cdict['robotpos']
        goalpos = cdict['goalpos']
        mainrobot = cdict['mainrobot']
        answer = cdict['answer']
        imgname = cdict['img']
        baseimgname = cdict['baseimg']

    for key in userdata.keys():
        setdefaultuser(userdata, key)

    
    assumed_solution = convertans(answer, robotpos)
    print(assumed_solution)

    while True:
        mentions = getmentions()
        if len(mentions) > 0:

            mentions.reverse()
            for stat in mentions:
                commandproc(userdata, stat, roundstart)

                if stat.in_reply_to_status_id != curproblemid:
                    continue
                
                setdefaultuser(userdata, stat.user.id_str, stat.user.screen_name)

                if problemname not in userdata[stat.user.id_str]['history']:
                    userdata[stat.user.id_str]['history'].append(problemname)

                ways = parsetext(stat.text, userdata[stat.user.id_str]['keyconfig'])

                if ways != -1:
                    waycou = checkanswer(mp,robotpos,goalpos,mainrobot, ways)
                    if waycou != -1:
                        absolutedofunc(api.create_favorite,stat.id)
                        text = "Accepted(" + str(waycou) + ' moves)'
                        if curshortest > waycou:
                            curshortest = waycou
                            text += '\nCurrently Shortest'
                            curshorteststat = stat
                            
                            if int(answer[0]) == waycou:
                                text += '\nOptimal'

                            absolutedofunc(api.update_status,text, in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
                            
                            if int(answer[0]) == waycou:
                                winproc(userdata, stat, problemname)
                                absolutedofunc(api.update_status,'Finished.\n🎉Winner ' + decoratename('@' + stat.user.screen_name, stat.user.id_str, userdata) + '\n' + 'https://twitter.com/' + stat.user.screen_name + '/status/' + str(stat.id), in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                                
                                gifurl = creategif(problemname, ways)
                                if gifurl != None:
                                    absolutedofunc(api.update_status,'gif\n'+gifurl['link'], in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                                
                                return


                #if ways == -1:
                #    text = "Invalid Format"
                #else:
                #    waycou = checkanswer(mp,robotpos,goalpos,mainrobot, ways)
                #    if waycou == -1:
                #        text = "Wrong Answer"
                #    else:
                #        text = "Accepted(" + str(waycou) + ' moves)'
                #        if curshortest > waycou:
                #            curshortest = waycou
                #            text += '\nCurrently Shortest'
                #            curshorteststat = stat
                #        elif curshortest != 10000000:
                #            text += '\nCurrently ' + str(curshortest) + ' moves is shortest'

                #        if int(answer[0]) == waycou:
                #            text += '\nOptimal'
                
                #if ways != -1:
                #    api.update_status(text, in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)

                #    if int(answer[0]) == waycou:
                #        winproc(userdata, stat, problemname)
                        
                #        api.update_status('Finished.\nWinner ' + decoratename('@' + stat.user.screen_name, stat.user.id_str, userdata) + '\n' + 'https://twitter.com/' + stat.user.screen_name + '/status/' + str(stat.id), in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                #        return
                
                #else:
                #    api.update_status(text, in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
                

        if datetime.now() >= timelimit:
            text = 'Timeup.\n'
            if curshorteststat != None:
                winproc(userdata, curshorteststat, problemname)
                text += '🎉Winner ' + decoratename('@' + curshorteststat.user.screen_name, curshorteststat.user.id_str, userdata) + '\n' + 'https://twitter.com/' + curshorteststat.user.screen_name + '/status/' + str(curshorteststat.id) + '\n'
            
            text += 'Answer:' + assumed_solution
            absolutedofunc( api.update_status,text, in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
            
            gifurl = creategif(problemname, parsetext(assumed_solution, {'u':0,'r':1,'d':2,'l':3}))
            if gifurl != None:
                absolutedofunc(api.update_status,'gif\n'+gifurl['link'], in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                                
            return

        time.sleep(1)

    return

def sleepwithlisten(sec, userdata, roundstart=-1):
    starttime = datetime.now()
    while (datetime.now() - starttime).total_seconds() < sec:
        mentions = getmentions()
        
        for stat in mentions:
            commandproc(userdata, stat, roundstart)
        time.sleep(1)
    return


CONSUMER_KEY = 'kNePGOncpjWFreJ328eyYohGz'
CONSUMER_SECRET = 'UT1iFpefTYbGfP2xL5hjGCYQnqNUku0XN3MA4Oi14nnc15WI5I'
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

redirect_url = auth.get_authorization_url()


#print('Get your verification code from: ' + redirect_url)

#verifier = input('Type the verification code: ').strip()

#auth.get_access_token(verifier)
print('input mode = [test:0, real:1]')

if int(input()) == 0:
    ACCESS_TOKEN = '1131066930478034944-dOEypEJR06qTos6usCQpvAqIgirZS8'
    ACCESS_SECRET = 'etEIzdmzHi99aTcgfkWmwmhEkDRbdT6r4FAc0lsaZYkmW'
else:
    ACCESS_TOKEN = '1117739551873568768-P7YUwZGNXQJ8Y7simuiGz91RjcJ42l'
    ACCESS_SECRET = 'bwqv9RLTVJcS0VN77RazaHKaqSXB5WYTUAbiy5ERrTZ4b'


auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

api = tweepy.API(auth, wait_on_rate_limit=True)

print('Done!')

getmentions.lastgettime = datetime(2000,10,1,0,0,0,0)
getmentions.lastid = api.mentions_timeline(count=1)[0].id


roundrange = [5,55]

with open('userdata.json') as f:
    userdata = json.load(f)
    while datetime.now().minute < roundrange[0] or datetime.now().minute >= roundrange[1]:
        sleepwithlisten(1, userdata)

roundstart = -1
timelimit = -1
roundname = str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour)

with open('rounds.json') as f:
    rounds = json.load(f)

if roundname in rounds.keys():
    roundstart = rounds[roundname]['roundstart']
    timelimit = datetime.strptime(rounds[roundname]['timelimit'], '%Y/%m/%d %H:%M:%S')

while True:
    
    if roundstart == -1:
        absolutedofunc(api.update_status,'Round ' + str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour))

    curproblemid, problemname = tweetnewproblem()

    if roundstart == -1:
        roundstart = int(problemname)
        roundname = str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour)
        timelimit = datetime.now()
        timelimit = datetime(timelimit.year, timelimit.month, timelimit.day, timelimit.hour, roundrange[1], 0, 0)
        
        with open('rounds.json', 'w') as f:
            rounds[roundname] = {}
            rounds[roundname]['roundstart'] = roundstart
            rounds[roundname]['timelimit'] = timelimit.strftime('%Y/%m/%d %H:%M:%S')
            json.dump(rounds,f)

    maincycle(timelimit, roundstart, curproblemid, problemname)
    
    with open('userdata.json') as f:
        userdata = json.load(f)
        if datetime.now() >= timelimit:
        
            tweetoverallranking(userdata, reply_id = tweethourlyranking(userdata, roundstart, basetext = 'Round ' + roundname + ' Finished\n').id)
            roundstart = -1
        
            sleepwithlisten(600, userdata)
        else:

            sleepwithlisten(20, userdata, roundstart)
