import tweepy
import time
import pymongo
import copy
import random
import ProblemGenerator
import re
from PIL import Image
from datetime import datetime
from imgurpython import ImgurClient

import utils
from datetime import datetime
import APIControler

def tweetnewproblem(ctrls):
    
    newprob = ctrls.db['problem'].find_one({'used':False})
    
    plist = list(ctrls.db['problem'].find({'used' : True}).sort('problem_num', direction=pymongo.DESCENDING) )
    if len(plist) == 0:
        newprob['problem_num'] = 1
    else:
        newprob['problem_num'] = [0]['problem_num'] + 1

    stat = utils.absolutedofunc(ctrls.twapi.update_with_media, filename=newprob['img'], status="Problem number:" + str(newprob['problem_num']))
    
    newprob['tweet_id'] = stat.id
    newprob['used'] = True
    ctrls.db['problem'].save(newprob)

    return stat.id, newprob['problem_num']

def startround(ctrls, roundstart, timelimit, roundname):

    while True:
        curproblemid, problem_num = tweetnewproblem(ctrls)

        maincycle(ctrls, timelimit, roundstart, curproblemid, problem_num)
        
        if datetime.now() >= timelimit:
        
            utils.tweetoverallranking(ctrls, reply_id = utils.tweethourlyranking(ctrls, roundstart, basetext = 'Round ' + roundname + ' Finished\n').id)
            roundstart = None

            return
        else:
            utils.sleepwithlisten(ctrls, 20, roundstart)

                
def winproc(ctrls, stat, problem_num):
    userdata = ctrls.getuser(stat.user.id_str)
    userdata[stat.user.id_str]['pointsum.Wanko-Soba']+=1
    userdata[stat.user.id_str]['winhistory'].append(problem_num)
    userdata[stat.user.id_str]['roundscore'] += 1

    sorteduser = sorted(userdata.items(), key=lambda x:x[1]['pointsum.Wanko-Soba'],reverse=True)

    realrank = 1
    buf = -1
    for i in range(len(sorteduser)):
        usr = sorteduser[i][0]
        if buf != userdata[usr]['wincount']:
            realrank = i + 1
        userdata[usr]['rank'] = realrank
        buf = userdata[usr]['wincount']
        
    ctrls.db['user'].save(userdata)
    return



def maincycle(ctrls, timelimit, roundstart, curproblemid, problem_num):
    curshortest = 10000000
    curshorteststat = None
            
    cdict = ctrls.db['problem'].find_one(problem_num)
    mp = cdict['board']
    robotpos = cdict['robotpos']
    goalpos = cdict['goalpos']
    mainrobot = cdict['mainrobot']
    answer = cdict['answer']
    imgname = cdict['img']
    baseimgname = cdict['baseimg']

    assumed_solution = utils.convertans(answer, robotpos)
    print(assumed_solution)

    while True:
        mentions = utils.getmentions(ctrls)
        if len(mentions) > 0:

            mentions.reverse()
            for stat in mentions:
                utils.commandproc(ctrls, stat, roundstart)

                if stat.in_reply_to_status_id != curproblemid:
                    continue
                
                utils.setdefaultuser(ctrls, stat.user.id_str, stat.user.screen_name)

                ctrls.db['user'].update_one({'user_id' : stat.user.id_str}, {'$put' : {'history': problem_num}})

                ways = utils.parsetext(stat.text, ctrls.getuser(stat.user.id_str)['keyconfig'])

                if ways != -1:
                    waycou = utils.checkanswer(mp,robotpos,goalpos,mainrobot, ways)
                    if waycou != -1:
                        utils.absolutedofunc(ctrls.twapi.create_favorite,stat.id)
                        text = "Accepted(" + str(waycou) + ' moves)'
                        if curshortest > waycou:
                            curshortest = waycou
                            text += '\nCurrently Shortest'
                            curshorteststat = stat
                            
                            if int(answer[0]) == waycou:
                                text += '\nOptimal'

                            utils.absolutedofunc(ctrls.twapi.update_status,text, in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
                            
                            if int(answer[0]) == waycou:
                                utils.winproc(ctrls, stat, problem_num)
                                utils.absolutedofunc(ctrls.twapi.update_status,'Finished.\n🎉Winner ' + utils.decoratename('@' + stat.user.screen_name, stat.user.id_str) + '\n' + 'https://twitter.com/' + stat.user.screen_name + '/status/' + str(stat.id), in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                                
                                gifid = utils.creategif(ctrls,problem_num, ways)
                                if gifid != None:
                                    utils.absolutedofunc(ctrls.twapi.update_status,'gif\n', media_ids = [gifid], in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                                
                                return

        if datetime.now() >= timelimit:
            text = 'Timeup.\n'
            if curshorteststat != None:
                utils.winproc(ctrls, curshorteststat, problem_num)
                text += '🎉Winner ' + utils.decoratename('@' + curshorteststat.user.screen_name, curshorteststat.user.id_str) + '\n' + 'https://twitter.com/' + curshorteststat.user.screen_name + '/status/' + str(curshorteststat.id) + '\n'
            
            text += 'Answer:' + assumed_solution
            utils.absolutedofunc( ctrls.twapi.update_status,text, in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
            
            gifid = utils.creategif(ctrls, problem_num, utils.parsetext(assumed_solution, {'u':0,'r':1,'d':2,'l':3}))
            if gifid != None:
                utils.absolutedofunc(ctrls.twapi.update_status,'gif', media_ids = [gifid], in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                                
            return

        time.sleep(1)

    return
