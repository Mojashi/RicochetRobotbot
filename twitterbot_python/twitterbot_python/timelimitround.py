import tweepy
import time
import math
import pymongo
import copy
import random
import ProblemGenerator
import re
from PIL import Image
from datetime import datetime
from imgurpython import ImgurClient

import utils

import APIControler

def tweetnewproblem(ctrls):
    
    #movecount = ProblemGenerator.ProblemGenerate('problems/' + str(len(history) + 1), 8)
    
    newprob = ctrls.db['problem'].find_one({'used':False})
    
    plist = list(ctrls.db['problem'].find({'used' : True}).sort('problem_num', direction=pymongo.DESCENDING) )
    if len(plist) == 0:
        newprob['problem_num'] = 1
    else:
        newprob['problem_num'] = [0]['problem_num'] + 1
    stat = utils.absolutedofunc(ctrls.twapi.update_with_media, filename=newprob['img'],
                               status="この問題の回答はリプライではなくDMで送信してください。\n制限時間は5分です。\nProblem number:" + str(newprob['problem_num']) + "\nOptimal:" +str(movecount) + 'moves\nhttps://twitter.com/messages/compose?recipient_id='+str(ctrls.dm_rec_id))
    
    newprob['tweet_id'] = stat.id
    newprob['used'] = True
    ctrls.db['problem'].save(newprob)

    return stat.id, newprob['problem_num']

def startround(ctrls, roundstart, timelimit, roundname):

    while True:
        curproblemid, problemname = tweetnewproblem(ctrls)

        maincycle(ctrls, timelimit, roundstart, curproblemid, problemname)
        
        if datetime.now() >= timelimit:
        
            utils.tweetoverallranking(ctrls, reply_id = utils.tweethourlyranking(ctrls, roundstart, basetext = 'Round ' + roundname + ' Finished\n').id)
            roundstart = None

            return
        else:
            utils.sleepwithlisten(ctrls, 5, roundstart)

def tweetproblemresult(ctrls, curproblemid, problemname, user_got_score):
    
    text = "Problem " + str(problemname) + " Result:\n"
    
    sortedscore = sorted(user_got_score.items(), key=lambda x:x[1],reverse=True)

    for po in sortedscore:
        text += utils.decoratename(ctrls, po[0]) + ' +' + str(po[1]) + 'pt → ' + str(ctrls.getuser(po[0])['roundscore']) + 'pt\n'

    utils.tweetlongtext(ctrls, status = text, in_reply_to_status_id = curproblemid)
    
    return


def checksubmissions(ctrls, start_timestamp, curproblemid, problem_num):
    
    problemend_timestamp = ctrls.dmapi.send_dm(ctrls.twapi.get_user(screen_name = 'oreha_senpai').id, 'problem ended')
        
    cdict = ctrls.db['problem'].find_one({'problem_num' : pproblem_num})

    mp = cdict['board']
    robotpos = cdict['robotpos']
    goalpos = cdict['goalpos']
    mainrobot = cdict['mainrobot']
    answer = cdict['answer']
    imgname = cdict['img']
    baseimgname = cdict['baseimg']

    assumed_solution = utils.convertans(answer, robotpos)
    
    text = 'Timeup.\n'
    text += 'Answer:' + assumed_solution
    utils.absolutedofunc( ctrls.twapi.update_status,text, in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
    
    gifid = utils.creategif(ctrls, problemname, utils.parsetext(assumed_solution, {'u':0,'r':1,'d':2,'l':3}))

    if gifid != None:
        utils.absolutedofunc(ctrls.twapi.update_status,'gif', media_ids = [gifid], in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
    
    utils.sleepwithlisten(ctrls,30)
    msgs = ctrls.dmapi.receive_dm(since_timestamp = start_timestamp, until_timestamp=problemend_timestamp)
    
    user_got_score = {}


    for msg in msgs:

        if str(msg['message_create']['sender_id']) == str(ctrls.dm_rec_id):
            continue

        print(msg)

        text = msg['message_create']['message_data']['text']
        user_id_str = str(msg['message_create']['sender_id'])
    

        screenname = ""
        if ctrls.getuser(user_id_str) == None:
            screenname =  utils.absolutedofunc(ctrls.twapi.get_user, user_id = int(user_id_str)).screen_name

        utils.setdefaultuser(ctrls, user_id_str, screenname)


        if problemname not in ctrls.getuser(user_id_str)['history']:
            ctrls.db['user'].update({'user_id':user_id_str}, {'$push' : {'history' : problem_num}})

        if user_id_str not in user_got_score.keys():
            user_got_score[user_id_str] = 0

        ways = utils.parsetext(text, ctrls.getuser(user_id_str)['keyconfig'])

        if ways != -1:
            waycou = utils.checkanswer(mp,robotpos,goalpos,mainrobot, ways)
            if waycou != -1:
                point = max(1, int(100 * math.pow(0.5, waycou - (len(answer) - 2))))

                user_got_score[user_id_str] = max(point , user_got_score[user_id_str])


    for key in user_got_score.keys():
        ctrls.db['user'].update({'user_id':key}, {'rondscore': user_got_score[key] + ctrls.getuser(key)['roundscore']})
        
    tweetproblemresult(ctrls, curproblemid, problemname, user_got_score)

    return

def maincycle(ctrls, timelimit, roundstart, curproblemid, problemname):
    
    with open('problems/' + problemname + '.json') as f:
        cdict = json.load(f)
        mp = cdict['board']
        robotpos = cdict['robotpos']
        goalpos = cdict['goalpos']
        mainrobot = cdict['mainrobot']
        answer = cdict['answer']
        imgname = cdict['img']
        baseimgname = cdict['baseimg']
        
    if ctrls.getuser(user_id_str) == None:
        utils.setdefaultuser(ctrls, key)

    assumed_solution = utils.convertans(answer, robotpos)
    print(assumed_solution)

    problemstart_timestamp = ctrls.dmapi.send_dm(ctrls.twapi.get_user(screen_name = 'oreha_senpai').id, 'problem started')


    #utils.sleepwithlisten(api, min(5 * 60, (timelimit - datetime.now()).total_seconds()), roundstart)
    utils.sleepwithlisten(ctrls, 5 * 60, roundstart)
    
    checksubmissions(ctrls, problemstart_timestamp, curproblemid, problemname)
    
    return
