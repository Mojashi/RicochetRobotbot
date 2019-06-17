import tweepy
import time
import msvcrt
import traceback
import json
import sys
import copy
import random
import re
from PIL import Image
from datetime import datetime
from datetime import timedelta
from imgurpython import ImgurClient
import pymongo
import directmessage

import APIControler


def absolutedofunc(func, *args, **kwargs):
    while True:
        try:
            ret = func(*args, **kwargs)
            return ret
        except:
            er = sys.exc_info()
            print(er)
      
            if er[1].api_code == 187:
                return


            for i in range(0, 60):
                if msvcrt.kbhit():
                    return

                time.sleep(1)
    return

def convert_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp) + timedelta(hours = 9)



def picknewproblem(ctrls, move):
    
    newprob = ctrls.db['problem'].find_one({'used':False, 'optimal_moves':move})
    
    if newprob == None:
      return None

    plist = list(ctrls.db['problem'].find({'used' : True}).sort('problem_num', direction=pymongo.DESCENDING) )
    if len(plist) == 0:
        newprob['problem_num'] = 1
    else:
        newprob['problem_num'] = plist[0]['problem_num'] + 1
    
    pics = GenerateImage(newprob['board'],newprob['goalpos'],newprob['robotpos'],newprob['mainrobot'])
    pics[0].save("problems/" + str(newprob['problem_num'])+'_base.png')
    pics[1].save("problems/" + str(newprob['problem_num'])+'.png')

    newprob['img'] = "problems/" + str(newprob['problem_num']) + '.png'
    newprob['baseimg'] = "problems/" + str(newprob['problem_num']) + '_base.png'
    
    newprob['used'] = True
    ctrls.db['problem'].save(newprob)

    return newprob

def accessdict(dict, keyword):
    def recfunc(dic, w):
        if len(w) == 1:
            return dic[w[0]]
        return recfunc(dic[w[0]], w[1:])
    
    return recfunc(dict,keyword.split('.'))

def getrank(ctrls, user_id, keyword = 'pointsum.Wanko-Soba'):
    pipe = [{'$match':{keyword: {'$gt':accessdict(ctrls.getuser(user_id),keyword)}}}, {'$count' : 'zrank'}]
    agg = list(ctrls.db['user'].aggregate(pipeline = pipe))
    if len(agg) == 0:
        return 1
    return agg[0]['zrank'] + 1

def decoratename(ctrls, userid_str, username = ''):
    user = ctrls.db['user'].find_one({'user_id':userid_str})

    if username == '':
        username = user['screen_name']

    rating = user['rating']
    with open('decorate.json',encoding="utf-8_sig") as f:
        decorate = json.load(f)
        for v in decorate.values():
            if v['range'][0] <= rating and v['range'][1] >= rating:
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


def creategif(ctrls, problem_num, ans):
    Dir = [[0,-1],[1,0],[0,1],[-1,0]]
    cdict = ctrls.db['problem'].find_one({'problem_num' : problem_num})

    mp = cdict['board']
    curpos = cdict['robotpos']
    goalpos = cdict['goalpos']
    mainrobot = cdict['mainrobot']
    answer = cdict['answer']
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
            imgs.append(GenerateImage(mp,goalpos,curpos, mainrobot, baseimgname)[1].resize((width,height)))
            
        imgs.append(GenerateImage(mp,goalpos,curpos, mainrobot, baseimgname)[1].resize((width,height)))
        imgs.append(GenerateImage(mp,goalpos,curpos, mainrobot, baseimgname)[1].resize((width,height)))
    
        curpos[num] = [int(curpos[num][0]),int(curpos[num][1])]

    imgs[0].save('buf.gif',save_all = True, append_images=imgs[1:], optimize=True,duration=70, loop = 0)
    

    try:
        return ctrls.dmapi.uploadmedia('buf.gif')
    except:
        er = sys.exc_info()
        print(er)
        return None
    return None

def tweethourlyranking(ctrls, fr, basetext="", reply_id=None):
    text = basetext + "\n"
    
    sorteduser = ctrls.db['user'].find({'history' : {'$gte' : fr}}).sort('roundscore', pymongo.DESCENDING)

    realrank = 1
    buf = -1
    cou = 0
    for user in list(sorteduser):
        score = user['roundscore']
        if score != buf:
            realrank = cou + 1
        text += str(realrank) + '. ' + decoratename(ctrls, user['user_id']) + ' ' + str(score) + 'pt\n'
        buf = score
        if cou == 9:
            break
        cou += 1

    if reply_id == None:
        return absolutedofunc(ctrls.twapi.update_status, text)
    else:
        return absolutedofunc(ctrls.twapi.update_status,text, in_reply_to_status_id = reply_id, auto_populate_reply_metadata=True)

def tweetoverallranking(ctrls,  basetext="", keyword = 'pointsum.Wanko-Soba',reply_id=None):
    text = "Overall Ranking:\n"
    
    sorteduser = ctrls.db['user'].find().sort(keyword, pymongo.DESCENDING)

    counter = 1
    currank = 1
    bef = 0
    for user in list(sorteduser):
        if bef != accessdict(user,keyword):
            currank = counter
        text += str(currank) + '. ' + decoratename(ctrls, user['user_id']) + ' ' + str(accessdict(user,keyword)) + 'pt\n'
        counter += 1
        bef = accessdict(user,keyword)
        if counter == 10:
            break

        
    if reply_id == None:
        return absolutedofunc(ctrls.twapi.update_status,text)
    else:
        return absolutedofunc(ctrls.twapi.update_status,text, in_reply_to_status_id = reply_id, auto_populate_reply_metadata=True)

def setdefaultuser(ctrls, user_id_str, screen_name=''):
    ctrls.db['user'].update({'user_id':user_id_str},{'$setOnInsert':
        {'user_id':user_id_str,
         'pointsum':{'Wanko-Soba':0,'Time-Limited':0}, 
         'screen_name':screen_name,
         'history':[], 
         'keyconfig':{'u':0,'r':1,'d':2,'l':3}, 
         'roundscore':0,
         'inner_rating':1200,
         'rating':0,
         'performance_history':[],
         'contest_history':[]}}, upsert = True)


def setdefaultcollection(ctrls):
    ctrls.db['user'].update_many({}, {'$setOnInsert' : {
         'pointsum':{'Wanko-Soba':0,'Time-Limited':0}, 
         'screen_name':'',
         'history':[], 
         'keyconfig':{'u':0,'r':1,'d':2,'l':3}, 
         'roundscore':0}}, upsert = True)
   

def commandproc(ctrls, stat, fr=-1):
    args = stat.text.split()
    while args[0][0] == '@':
        args.pop(0)

    if len(args) == 0:
        return

    if args[0] == '!myrank':
        setdefaultuser(ctrls, stat.user.id_str, stat.user.screen_name)
        absolutedofunc(ctrls.twapi.update_status,
                       'Rating: ' + str(ctrls.getuser(stat.user.id_str)['rating']) + ' Rank' + str(getrank(ctrls, stat.user.id_str, 'rating')) + 
                       '\nWanko-Soba: ' + str(ctrls.getuser(stat.user.id_str)['pointsum']['Wanko-Soba']) + 'pt Rank' + str(getrank(ctrls, stat.user.id_str, 'pointsum.Wanko-Soba')) + 
                       '\nTime-Limited: ' + str(ctrls.getuser(stat.user.id_str)['pointsum']['Time-Limited']) + 'pt Rank' + str(getrank(ctrls, stat.user.id_str, 'pointsum.Time-Limited'))
                       , in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
    
    elif args[0] == '!ありがとう' or args[0] == '!thank':
        absolutedofunc(ctrls.twapi.update_status,'どういたしまして', in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
    
    elif args[0] == '!omikuji':
        kuji = ['Daikichi', 'Chukichi', 'Shokichi', 'Suekichi', 'Kyo', 'Daikyo']
        absolutedofunc(ctrls.twapi.update_status,kuji[random.randint(0, len(kuji) - 1)], in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
    
    elif args[0] == '!ranking':
        if len(args) >= 2:
            if args[1] == 'wankosoba':
                tweetoverallranking(ctrls, 'Wanko-Soba Ranking', 'pointsum.Wanko-Soba', reply_id = stat.id)
        
            elif args[1] == 'timelimited':
                tweetoverallranking(ctrls, 'Time-Limited Ranking', 'pointsum.Time-Limited', reply_id = stat.id)
        
            elif args[1] == 'rating':
                tweetoverallranking(ctrls, 'Rating Ranking', 'rating', reply_id = stat.id)

            elif fr != -1 and args[1] == 'round':
                tweethourlyranking(ctrls, fr, reply_id = stat.id)

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
                    absolutedofunc(ctrls.twapi.update_status, hand[0] + '\n' + wintable[args[1]][hand[1]], in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)

    elif args[0] == '!setting':
        if len(args) <= 1:
            return
        setdefaultuser(ctrls, stat.user.id_str, stat.user.screen_name)

        if args[1] == 'wasd':
            ctrls.db['user'].update({'user_id' : stat.user.id_str},{'$set' : {'keyconfig' : {'w':0,'d':1,'s':2,'a':3}}})
            absolutedofunc(ctrls.twapi.create_favorite,stat.id)
    
        elif args[1] == 'urdl':
            ctrls.db['user'].update({'user_id' : stat.user.id_str},{'$set' : {'keyconfig' :{'u':0,'r':1,'d':2,'l':3}}})
            absolutedofunc(ctrls.twapi.create_favorite,stat.id)
            
        elif args[1] == 'hjkl':
            ctrls.db['user'].update({'user_id' : stat.user.id_str},{'$set' : {'keyconfig' :{'k':0,'l':1,'j':2,'h':3}}})
            absolutedofunc(ctrls.twapi.create_favorite,stat.id)


    #elif args[0] == '!gif':
    #    rpd = ctrls.twapi.get_status(stat.in_reply_to_status_id)
    #    gifid = None

    #    algif = ctrls.db['gif'].find_one({'answer_tweet_id':rpd.id_str})
    #    if algif != None:
    #        gifid = algif['gif_id']

    #    print("gif")
    #    if gifid == None:
    #        setdefaultuser(ctrls,rpd.user.id_str, rpd.user.screen_name)
    #        ans = parsetext(rpd.text, cutrls.getuser(rpd.user.id_str)['keyconfig'])
    #        if ans != -1:
    #            with open('history.json','r') as f:
    #                history = json.load(f)
    #                probnamelis = [k for k, v in history.items() if v == rpd.in_reply_to_status_id]
    #                if len(probnamelis) > 0:
    #                    gifid = creategif(ctrls, probnamelis[0], ans)
    #                    algif[rpd.id_str] = gifid

    #                    with open('gifs.json','w') as f:
    #                         json.dump(algif, f)
    
    #    if gifid != None:
    #        absolutedofunc(ctrls.twapi.update_status,'gif', media_ids = [gifid],in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)

    return

def convertans(answer, robotpos):
    Dir = {'u':[0,-1],'r':[1,0],'d':[0,1],'l':[-1,0]}
    curpos = copy.copy(robotpos)

    ret = ''
    for i in range(len(answer)):
        nex = answer[i]
        num,y,x = [int(x) for x in nex.split(' ')]
        
        for itr in Dir.items():
            if itr[1] == [(x - curpos[num][0] > 0) - (x - curpos[num][0] < 0),(y - curpos[num][1] > 0) - (y - curpos[num][1] < 0)]:
                ret += str(num) + itr[0] + ','
                curpos[num] = [x,y]
                break

    return ret.rstrip(',')

def getmentions(ctrls):

    if (datetime.now() - getmentions.lastgettime).total_seconds() >= 15:
        mentions = absolutedofunc(ctrls.twapi.mentions_timeline,since_id=getmentions.lastid, count=199)
        for stat in mentions:
            print("from:" + stat.user.screen_name + " " + stat.text)
        getmentions.lastgettime = datetime.now()
        if len(mentions) > 0:
            getmentions.lastid = mentions[0].id
        return mentions

    return []

   

def sleepwithlisten(ctrls,sec, roundstart=-1):
    starttime = datetime.now()
    while (datetime.now() - starttime).total_seconds() < sec:
        mentions = getmentions(ctrls)
        
        for stat in mentions:
            commandproc(ctrls, stat, roundstart)
        time.sleep(1)
    return

def tweetlongtext(ctrls, **kwargs):
    text = kwargs['status']
    beforestat = None
    cursor = 0
    while cursor < len(text):
        nexcursor = min(cursor + 200, len(text))
        curtext = text[cursor:nexcursor]
        print(curtext)
        cursor = nexcursor
        
        if beforestat != None:
            kwargs['in_reply_to_status_id'] = beforestat.id

        kwargs['status'] = curtext
        beforestat = absolutedofunc(ctrls.twapi.update_status, **kwargs)

    return beforestat


def GenerateImage(mp, goalpos, robotpos, mainrobot, baseimgname = ''):
    
    robotimg = [Image.open('img/robot/blue.png'),Image.open('img/robot/red.png'),Image.open('img/robot/green.png'),Image.open('img/robot/yellow.png'),Image.open('img/robot/black.png')]
    width = robotimg[0].width
    height = robotimg[0].height

    ret = Image.new('RGB', (width * 16, height*16))

    if baseimgname == '':
        groundimg = Image.open('img/ground.png')
        wallimg = Image.open('img/wall.png')
        goalimg = Image.open('img/goal.png')
        centerimg = Image.open('img/center.png');
        
        markimg = [Image.open('img/mark/blue.png'),Image.open('img/mark/red.png'),Image.open('img/mark/green.png'),Image.open('img/mark/yellow.png'),Image.open('img/mark/black.png')]

        
        
        for i in range(16):
            for j in range(16):
                if (i==7 or i==8) and (j == 7 or j == 8):
                    ret.paste(centerimg, (i*width, j*height))
                else:
                    ret.paste(groundimg, (i*width, j*height))
                    for k in range(4):
                        if mp[i][j][k] == 1:
                            ret.paste(wallimg.rotate(k * -90), (i*width, j*height), wallimg.rotate(k * -90).split()[3])

        ret.paste(markimg[mainrobot], (int(7.5*width), int(7.5*height)), markimg[mainrobot].split()[3]);
        ret.paste(goalimg,  (goalpos[0]*width, goalpos[1]*height), goalimg.split()[3])
        
        baseimg = copy.copy(ret)
    else:
        baseimg = Image.open(baseimgname)
        ret = Image.open(baseimgname)

    for i in range(5):
        ret.paste(robotimg[i], (int(robotpos[i][0]*width), int(robotpos[i][1]*height)), robotimg[i].split()[3])

    return baseimg,ret
