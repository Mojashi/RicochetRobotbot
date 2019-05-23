import tweepy
import time
import subprocess
import json
import copy
import ProblemGenerator
from PIL import Image
from datetime import datetime

def decoratename(username, userid_str, userdata):
    with open('decorate.json') as f:
        decorate = json.load(f)
        for v in decorate.values():
            if v['range'][0] <= userdata[userid_str]['rank'] and v['range'][1] >= userdata[userid_str]['rank']:
                return v['deco'].replace('%user', username)
    return username

def checkanswer(mp, robotpos, goalpos, mainrobot, ans):
    Dirnum = {'u':0,'r':1, 'd':2,'l':3}
    Dir = [[0,-1],[1,0],[0,1],[-1,0]]

    curpos = copy.copy(robotpos)

    for way in ans:
        if len(way) != 2:
            return -2
        if not(ord(way[0])>=ord('0') and ord(way[0]) <= ord('4')):
            return -2
        if way[1] !='u' and way[1] !='r' and way[1] !='d' and way[1] !='l':
            return -2

        num = int(way[0])
        d = Dirnum[way[1]]

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
    
    stat = api.update_with_media(filename='problems/'+str(len(history) + 1)+'.png', status="Problem number:"+str(len(history) + 1))

    history[len(history) + 1] = stat.id

    with open('history.json','w') as f:
        json.dump(history, f)

    return stat.id, str(len(history))

def creategif(mp, robotpos, goalpos, mainrobot, imgname, baseimgname, ans):
    Dirnum = {'u':0,'r':1, 'd':2,'l':3}
    Dir = [[0,-1],[1,0],[0,1],[-1,0]]
    
    curpos = copy.copy(robotpos)
    fimg =Image.open(imgname)
    width = int(fimg.width/2)
    height= int(fimg.height/2)
    imgs = [fimg.resize((width,height))]
    

    for way in ans:
        num = int(way[0])
        d = Dirnum[way[1]]

        fr = curpos[num]
        to = curpos[num]
        while True:
            nex = [to[0] + Dir[d][0], to[1] + Dir[d][1]]
            if mp[to[0]][to[1]][d] == 1 or nex in curpos:
                break
            to = nex

        while [int(fr[0]*10),int(fr[1]*10)] != [int(to[0]*10),int(to[1]*10)]:
            nex = [fr[0] + Dir[d][0]/1.0, fr[1] + Dir[d][1]/1.0]
            fr = nex
            curpos[num] = fr
            imgs.append(ProblemGenerator.GenerateImage(mp,goalpos,curpos, mainrobot, baseimgname)[1].resize((width,height)))
            
        imgs.append(ProblemGenerator.GenerateImage(mp,goalpos,curpos, mainrobot, baseimgname)[1].resize((width,height)))
        imgs.append(ProblemGenerator.GenerateImage(mp,goalpos,curpos, mainrobot, baseimgname)[1].resize((width,height)))
    
        curpos[num] = [int(curpos[num][0]),int(curpos[num][1])]

    imgs[0].save('buf.gif', save_all = True, append_images=imgs[1:], optimize=True,duration=50)

    return

def tweethourlyranking(userdata, fr, basetext = "", reply_id = None):
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
        cou += 1
        text += str(realrank) + '. ' + decoratename(usr['screen_name'], sorteduser[i][0], userdata) + ' ' + str(winc)+ 'win\n'
        buf = winc
        if cou == 9:
            break

    if reply_id == None:
        return api.update_status(text)
    else:
        return api.update_status(text, in_reply_to_status_id = reply_id, auto_populate_reply_metadata=True)

def tweetoverallranking(userdata, basetext = "", reply_id = None):
    text = "Overall Ranking:\n"
    
    sorteduser = sorted(userdata.items(), key=lambda x:x[1]['wincount'],reverse=True)
    for i in range(len(sorteduser)):
        usr = userdata[sorteduser[i][0]]
        text += str(usr['rank']) + '. ' + decoratename(usr['screen_name'], sorteduser[i][0], userdata) + ' ' + str(usr['wincount']) + 'win\n'
        if i == 9:
            break

        
    if reply_id == None:
        return api.update_status(text)
    else:
        return api.update_status(text, in_reply_to_status_id = reply_id, auto_populate_reply_metadata=True)
                
#def createuser(userdata, usr):
#    userdata[usr.id_str] = {}
#    userdata[usr.id_str]['rank'] = 9999999
#    userdata[usr.id_str]['wincount'] = 0
#    userdata[usr.id_str]['screen_name'] = usr.screen_name
#    userdata[usr.id_str]['history'] = []
#    userdata[usr.id_str]['winhistory'] = []

def setdefaultuser(userdata, usr_id_str, usr_name = ''):
    userdata.setdefault(usr_id_str, {})
    userdata[usr_id_str].setdefault('rank', 9999999)
    userdata[usr_id_str].setdefault('wincount', 0)
    userdata[usr_id_str].setdefault('screen_name', usr_name)
    userdata[usr_id_str].setdefault('history', [])
    userdata[usr_id_str].setdefault('winhistory', [])

def commandproc(userdata, stat, fr):
    if stat.text.split()[1] == '!myrank':
        setdefaultuser(userdata, stat.user.id_str, stat.user.screen_name)
        api.update_status('Wins:'+ str(userdata[stat.user.id_str]['wincount']) + '\nRank:' + str(userdata[stat.user.id_str]['rank']), in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
    
    if stat.text.split()[1] == '!roundrank':
        tweethourlyranking(userdata, fr, reply_id = stat.id)

    if stat.text.split()[1] == '!overallrank':
        tweetoverallranking(userdata, reply_id = stat.id)

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

def maincycle(timelimit, roundstart, curproblemid, problemname):
    curshortest = 10000000
    lastid = curproblemid
    
    with open('userdata.json') as f:
        userdata = json.load(f)
            
    with open('problems/'+problemname+'.json') as f:
        cdict = json.load(f)
        mp = cdict['board']
        robotpos = cdict['robotpos']
        goalpos = cdict['goalpos']
        mainrobot = cdict['mainrobot']
        answer =  cdict['answer']
        imgname = cdict['img']
        baseimgname = cdict['baseimg']

    for key in userdata.keys():
        setdefaultuser(userdata, key)

    
    assumed_solution = convertans(answer, robotpos)
    print(assumed_solution)
    while True:
        mentions = api.mentions_timeline(since_id=lastid)
        if len(mentions) > 0:
            lastid = mentions[0].id
            mentions.reverse()
            for stat in mentions:
                commandproc(userdata, stat, roundstart)

                if stat.in_reply_to_status_id != curproblemid:
                    continue
                
                setdefaultuser(userdata, stat.user.id_str, stat.user.screen_name)

                if problemname not in userdata[stat.user.id_str]['history']:
                    userdata[stat.user.id_str]['history'].append(problemname)

                print("from:"+stat.user.screen_name + " " + stat.text)

                ways =stat.text.split()
                while ways[0][0] == '@':
                    ways.pop(0)
                curans = ways[0].split(',')

                waycou = checkanswer(mp,robotpos,goalpos,mainrobot,curans)
                if waycou == -2:
                    text = "Invalid Format"
                elif waycou == -1:
                    text = "Wrong Answer"
                else:
                    text = "Accepted(" + str(waycou) + ' moves)'
                    if curshortest > waycou:
                        curshortest = waycou
                        text += '\nCurrently Shortest'
                    elif curshortest != 10000000:
                        text += '\nCurrently ' + str(curshortest) + ' moves is shortest'

                    if int(answer[0]) == waycou:
                        text += '\nOptimal'
                
                if waycou == -1 or waycou >= 0:
                    #creategif(mp,robotpos,goalpos,mainrobot,imgname,baseimgname,curans)
                    #try:
                    #    mediaresp = api.media_upload(filename='2019-04-15 00-36-38.mp4')
                    #    api.update_status(text, in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True, media_ids=[mediaresp['media_id']])
                    #except:
                    api.update_status(text, in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
                else:
                    api.update_status(text, in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
                
                if int(answer[0]) == waycou:
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
                        
                    api.update_status('Finished.\nWinner '+decoratename('@'+stat.user.screen_name, stat.user.id_str, userdata) + '\n'+'https://twitter.com/'+stat.user.screen_name + '/status/' + str(stat.id), in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                


                    return

        if datetime.now() >= timelimit:
            api.update_status('Timeup.\nAnswer:'+assumed_solution, in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
            return
        time.sleep(15)


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

api = tweepy.API(auth)

print('Done!')


roundrange = [5,55]

while datetime.now().minute < roundrange[0] or datetime.now().minute >= roundrange[1]:
    time.sleep(1)

roundstart = -1
timelimit = -1
roundname = str(datetime.now().year)+ str(datetime.now().month)+ str(datetime.now().day)+ str(datetime.now().hour)

with open('rounds.json') as f:
    rounds = json.load(f)

if roundname in rounds.keys():
    roundstart = rounds[roundname]['roundstart']
    timelimit = datetime.strptime(rounds[roundname]['timelimit'], '%Y/%m/%d %H:%M:%S')

while True:
    
    if roundstart == -1:
        api.update_status('Round ' + str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour))

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
    
    if datetime.now() >= timelimit:
        with open('userdata.json') as f:
            userdata = json.load(f)
        
        tweetoverallranking(userdata, reply_id = tweethourlyranking(userdata, roundstart, basetext = 'Round ' + roundname + ' Finished\n').id)
        roundstart = -1

        time.sleep(600)
