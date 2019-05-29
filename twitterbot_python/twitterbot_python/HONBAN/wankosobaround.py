import tweepy
import time

import json
import copy
import random
import ProblemGenerator
import re
from PIL import Image
from datetime import datetime
from imgurpython import ImgurClient

import utils
from datetime import datetime

def tweetnewproblem(api):
    
    with open('history.json','r') as f:
        history = json.load(f)

    ProblemGenerator.ProblemGenerate('problems/' + str(len(history) + 1))
    
    stat = utils.absolutedofunc(api.update_with_media, filename='problems/' + str(len(history) + 1) + '.png', status="Problem number:" + str(len(history) + 1))

    history[len(history) + 1] = stat.id

    with open('history.json','w') as f:
        json.dump(history, f)

    return stat.id, str(len(history))


def wankoround(api, timelimit, roundstart, curproblemid, problemname):
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
        utils.setdefaultuser(userdata, key)

    
    assumed_solution = utils.convertans(answer, robotpos)
    print(assumed_solution)

    while True:
        mentions = utils.getmentions(api)
        if len(mentions) > 0:

            mentions.reverse()
            for stat in mentions:
                utils.commandproc(api, userdata, stat, roundstart)

                if stat.in_reply_to_status_id != curproblemid:
                    continue
                
                utils.setdefaultuser(userdata, stat.user.id_str, stat.user.screen_name)

                if problemname not in userdata[stat.user.id_str]['history']:
                    userdata[stat.user.id_str]['history'].append(problemname)

                ways = utils.parsetext(stat.text, userdata[stat.user.id_str]['keyconfig'])

                if ways != -1:
                    waycou = utils.checkanswer(mp,robotpos,goalpos,mainrobot, ways)
                    if waycou != -1:
                        utils.absolutedofunc(api.create_favorite,stat.id)
                        text = "Accepted(" + str(waycou) + ' moves)'
                        if curshortest > waycou:
                            curshortest = waycou
                            text += '\nCurrently Shortest'
                            curshorteststat = stat
                            
                            if int(answer[0]) == waycou:
                                text += '\nOptimal'

                            utils.absolutedofunc(api.update_status,text, in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
                            
                            if int(answer[0]) == waycou:
                                utils.winproc(userdata, stat, problemname)
                                utils.absolutedofunc(api.update_status,'Finished.\n🎉Winner ' + utils.decoratename('@' + stat.user.screen_name, stat.user.id_str, userdata) + '\n' + 'https://twitter.com/' + stat.user.screen_name + '/status/' + str(stat.id), in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                                
                                gifurl = utils.creategif(problemname, ways)
                                if gifurl != None:
                                    utils.absolutedofunc(api.update_status,'gif\n'+gifurl['link'], in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                                
                                return

        if datetime.now() >= timelimit:
            text = 'Timeup.\n'
            if curshorteststat != None:
                utils.winproc(userdata, curshorteststat, problemname)
                text += '🎉Winner ' + utils.decoratename('@' + curshorteststat.user.screen_name, curshorteststat.user.id_str, userdata) + '\n' + 'https://twitter.com/' + curshorteststat.user.screen_name + '/status/' + str(curshorteststat.id) + '\n'
            
            text += 'Answer:' + assumed_solution
            utils.absolutedofunc( api.update_status,text, in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
            
            gifurl = utils.creategif(problemname, utils.parsetext(assumed_solution, {'u':0,'r':1,'d':2,'l':3}))
            if gifurl != None:
                utils.absolutedofunc(api.update_status,'gif\n'+gifurl['link'], in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                                
            return

        time.sleep(1)

    return
