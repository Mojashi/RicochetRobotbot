import tweepy
import time
import pymongo
import copy
import random
import re
from PIL import Image
from datetime import datetime
from imgurpython import ImgurClient
import random
import utils
from datetime import datetime
import APIControler

def tweetnewproblem(ctrls):
    
    newprob = None
    while newprob == None:
        newprob = utils.picknewproblem(ctrls, random.randint(5, 14))

    stat = utils.absolutedofunc(ctrls.twapi.update_with_media, filename=newprob['img'], status="Problem number:" + str(newprob['problem_num']))
    
    newprob['tweet_id'] = stat.id
    ctrls.db['problem'].save(newprob)

    return stat.id, newprob['problem_num']

def startround(ctrls, roundstart, timelimit, roundname):

    while True:
        curproblemid, problem_num = tweetnewproblem(ctrls)

        maincycle(ctrls, timelimit, roundstart, curproblemid, problem_num)
        
        if datetime.now() >= timelimit:
        
            utils.tweetoverallranking(ctrls,'Wanko-Soba Ranking', keyword = 'pointsum.Wanko-Soba', reply_id = utils.tweethourlyranking(ctrls, roundstart, basetext = 'Round ' + roundname + ' Finished\n').id)
            roundstart = None

            return
        else:
            utils.sleepwithlisten(ctrls, 20, roundstart)


def maincycle(ctrls, timelimit, roundstart, curproblemid, problem_num):
    curshortest = 10000000
    curshorteststat = None
            
    cdict = ctrls.db['problem'].find_one({'problem_num':problem_num})
    mp = cdict['board']
    robotpos = cdict['robotpos']
    goalpos = cdict['goalpos']
    mainrobot = cdict['mainrobot']
    answer = cdict['answer']
    imgname = cdict['img']
    baseimgname = cdict['baseimg']
    optimal_moves = cdict['optimal_moves']

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

                ctrls.db['user'].update_one({'user_id' : stat.user.id_str}, {'$addToSet' : {'history': problem_num}})

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
                            

                            if optimal_moves == waycou:
                                text += '\nOptimal'

                            utils.absolutedofunc(ctrls.twapi.update_status,text, in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
                            
                            if optimal_moves == waycou:
                                
                                ctrls.db['user'].update_one({'user_id' : stat.user.id_str}, {'$inc':{'roundscore': 1}})
                                ctrls.db['user'].update_one({'user_id' : stat.user.id_str}, {'$inc':{'pointsum.Wanko-Soba' : 1}})

                                utils.absolutedofunc(ctrls.twapi.update_status,'Finished.\n🎉Winner ' + utils.decoratename(ctrls, stat.user.id_str,username = '@' + stat.user.screen_name) + '\n' + 'https://twitter.com/' + stat.user.screen_name + '/status/' + str(stat.id), in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                                
                                gifid = utils.creategif(ctrls,problem_num, ways)
                                if gifid != None:
                                    utils.absolutedofunc(ctrls.twapi.update_status,'gif\n', media_ids = [gifid], in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                                
                                return

        if datetime.now() >= timelimit:
            text = 'Timeup.\n'
            if curshorteststat != None:
                ctrls.db['user'].update_one({'user_id' : curshorteststat.user.id_str}, {'$inc':{'roundscore': 1}})
                ctrls.db['user'].update_one({'user_id' : curshorteststat.user.id_str}, {'$inc':{'pointsum.Wanko-Soba' : 1}})
                text += '🎉Winner ' + utils.decoratename(ctrls, curshorteststat.user.id_str, username = '@' + curshorteststat.user.screen_name) + '\n' + 'https://twitter.com/' + curshorteststat.user.screen_name + '/status/' + str(curshorteststat.id) + '\n'
            
            text += 'Answer:' + assumed_solution
            utils.absolutedofunc( ctrls.twapi.update_status,text, in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
            
            gifid = utils.creategif(ctrls, problem_num, utils.parsetext(assumed_solution, {'u':0,'r':1,'d':2,'l':3}))
            if gifid != None:
                utils.absolutedofunc(ctrls.twapi.update_status,'gif', media_ids = [gifid], in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                                
            return

        time.sleep(1)

    return
