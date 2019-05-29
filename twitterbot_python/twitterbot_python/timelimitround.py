import tweepy
import time
import math

import json
import copy
import random
import ProblemGenerator
import re
from PIL import Image
from datetime import datetime
from imgurpython import ImgurClient

import utils


def tweetnewproblem(api, dm_rec_id):
    
    with open('history.json','r') as f:
        history = json.load(f)

    ProblemGenerator.ProblemGenerate('problems/' + str(len(history) + 1), 8)
    
    stat = utils.absolutedofunc(api.update_with_media, filename='problems/' + str(len(history) + 1) + '.png',
                               status="この問題の回答はリプライではなくDMで送信してください。\n制限時間は5分です。\nProblem number:" + str(len(history) + 1) + '\nhttps://twitter.com/messages/compose?recipient_id='+str(dm_rec_id))

    history[len(history) + 1] = stat.id

    with open('history.json','w') as f:
        json.dump(history, f)

    return stat.id, str(len(history))

def startround(api, dmapi, roundstart, timelimit, roundname, dm_rec_id):

    while True:
        curproblemid, problemname = tweetnewproblem(api, dm_rec_id)

        maincycle(api,dmapi, timelimit, roundstart, curproblemid, problemname, dm_rec_id)
        
        with open('userdata.json') as f:
            userdata = json.load(f)
            if datetime.now() >= timelimit:
            
                utils.tweetoverallranking(api, userdata, reply_id = utils.tweethourlyranking(api, userdata, roundstart, basetext = 'Round ' + roundname + ' Finished\n').id)
                roundstart = None

                return
            else:
                utils.sleepwithlisten(api,5, userdata, roundstart)

def tweetproblemresult(api, userdata, curproblemid, problemname, user_got_score):
    
    text = "Problem " + str(problemname) + " Result:\n"
    
    sortedscore = sorted(user_got_score.items(), key=lambda x:x[1],reverse=True)

    for po in sortedscore:
        text += utils.decoratename(userdata[po[0]]['screen_name'], po[0], userdata) + ' +' + str(po[1]) + 'pt → ' + str(userdata[po[0]]['roundscore']) + 'pt\n'

    utils.tweetlongtext(api, status = text, in_reply_to_status_id = curproblemid)
    
    return


def checksubmissions(api, dmapi, start_timestamp, curproblemid, problemname, dm_rec_id):
    
    problemend_timestamp = dmapi.send_dm(api.get_user(screen_name = 'oreha_senpai').id, 'problem ended')
        
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
        utils.setdefaultuser(userdata, key)

    assumed_solution = utils.convertans(answer, robotpos)
    

    text = 'Timeup.\n'
    text += 'Answer:' + assumed_solution
    utils.absolutedofunc( api.update_status,text, in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
    
    gifurl = utils.creategif(problemname, utils.parsetext(assumed_solution, {'u':0,'r':1,'d':2,'l':3}))
    if gifurl != None:
        utils.absolutedofunc(api.update_status,'gif\n'+gifurl['link'], in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
    
    
    utils.sleepwithlisten(api,30, userdata)
    msgs = dmapi.receive_dm(since_timestamp = start_timestamp, until_timestamp=problemend_timestamp)
    

    user_got_score = {}

    for msg in msgs:

        if str(msg['message_create']['sender_id']) == str(dm_rec_id):
            continue

        print(msg)

        text = msg['message_create']['message_data']['text']
        user_id_str = str(msg['message_create']['sender_id'])
    

        screenname = ""
        if user_id_str not in userdata:
            screenname =  utils.absolutedofunc(api.get_user, user_id = int(user_id_str)).screen_name

        utils.setdefaultuser(userdata, user_id_str, screenname)


        if problemname not in userdata[user_id_str]['history']:
            userdata[user_id_str]['history'].append(problemname)

        if user_id_str not in user_got_score.keys():
            user_got_score[user_id_str] = 0

        ways = utils.parsetext(text, userdata[user_id_str]['keyconfig'])

        if ways != -1:
            waycou = utils.checkanswer(mp,robotpos,goalpos,mainrobot, ways)
            if waycou != -1:
                point = max(1, int(100 * math.pow(0.5, waycou - (len(answer) - 2))))

                user_got_score[user_id_str] = max(point , user_got_score[user_id_str])


    for key in user_got_score.keys():
        userdata[key]['roundscore'] += user_got_score[key]
        
    with open('userdata.json', 'w') as f:
        json.dump(userdata, f)
        
    tweetproblemresult(api, userdata, curproblemid, problemname, user_got_score)

    return

def maincycle(api, dmapi, timelimit, roundstart, curproblemid, problemname, dm_rec_id):
    
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
        utils.setdefaultuser(userdata, key)

    assumed_solution = utils.convertans(answer, robotpos)
    print(assumed_solution)

    problemstart_timestamp = dmapi.send_dm(api.get_user(screen_name = 'oreha_senpai').id, 'problem started')


    #utils.sleepwithlisten(api, min(5 * 60, (timelimit - datetime.now()).total_seconds()), userdata, roundstart)
    utils.sleepwithlisten(api, 5 * 60, userdata, roundstart)
    
    checksubmissions(api, dmapi, problemstart_timestamp, curproblemid, problemname, dm_rec_id)
    
    return
