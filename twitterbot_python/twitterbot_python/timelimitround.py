import tweepy
import time
import math
import pymongo
import copy
import random
import re
from PIL import Image
from datetime import datetime
from imgurpython import ImgurClient

import utils
import webhook_receiver
import APIControler

def tweetnewproblem(ctrls, enable_torus, enable_mirror):
    
    #movecount = ProblemGenerator.ProblemGenerate('problems/' + str(len(history) + 1), 8)
    
    
    newprob = None
    while newprob == None:
        newprob = utils.picknewproblem(ctrls, random.randint(9, 16), enable_torus, enable_mirror)


    stat = utils.absolutedofunc(ctrls.twapi.update_with_media, filename=newprob['img'],
                               status="この問題の回答はリプライではなくDMで送信してください。\n制限時間は5分です。\nProblem number:" + str(newprob['problem_num']) + "\nOptimal:" +str(newprob['optimal_moves']) + 'moves\nhttps://twitter.com/messages/compose?recipient_id='+str(ctrls.dm_rec_id))
    
    newprob['tweet_id'] = stat.id
    ctrls.db['problem'].save(newprob)

    return stat.id, newprob['problem_num']

def startround(ctrls, roundstart, timelimit, roundname):
    
    enable_torus =random.randint(0,2) > 1
    enable_mirror =random.randint(0,2) > 1

    while True:

        maincycle(ctrls, timelimit, roundstart, enable_torus, enable_mirror)
        
        if datetime.now() >= timelimit:
        
            utils.tweetoverallranking(ctrls,'Time-Limited Ranking',keyword = 'pointsum.Time-Limited', reply_id = utils.tweethourlyranking(ctrls, roundstart, basetext = 'Round ' + roundname + ' Finished\n').id)
            roundstart = None

            return
        else:
            utils.sleepwithlisten(ctrls, 5, roundstart)

def tweetproblemresult(ctrls, curproblemid, problem_num, user_got_score):
    
    text = "Problem " + str(problem_num) + " Result:\n"
    
    sortedscore = sorted(user_got_score.items(), key=lambda x:x[1],reverse=True)

    for po in sortedscore:
        text += utils.decoratename(ctrls, po[0]) + ' +' + str(po[1]) + 'pt → ' + str(ctrls.getuser(po[0])['roundscore']) + 'pt\n'

    utils.tweetlongtext(ctrls, status = text, in_reply_to_status_id = curproblemid)
    
    return

def maincycle(ctrls, timelimit, roundstart, enable_torus, enable_mirror):
    
    
    que = webhook_receiver.start(ctrls)
    
    curproblemid, problem_num = tweetnewproblem(ctrls, enable_torus, enable_mirror)

    cdict = ctrls.db['problem'].find_one({'problem_num':problem_num})
    mp = cdict['board']
    robotpos = cdict['robotpos']
    goalpos = cdict['goalpos']
    mainrobot = cdict['mainrobot']
    answer = cdict['answer']
    imgname = cdict['img']
    baseimgname = cdict['baseimg']
    optimal_moves = cdict['optimal_moves']
    
    start_time = datetime.now()

    user_got_score = {}
        
    assumed_solution = utils.convertans(cdict)
    print(assumed_solution)

    problemstart_timestamp = ctrls.dmapi.send_dm(ctrls.twapi.get_user(screen_name = 'oreha_senpai').id, 'problem started')

    problem_length = 5 * 60
    point_rate = [100, 60]

    #utils.sleepwithlisten(api, min(5 * 60, (timelimit - datetime.now()).total_seconds()), roundstart)
    #utils.sleepwithlisten(ctrls, 5 * 60, roundstart)
    

    while True:

        while que.empty() == False:
            msgs = webhook_receiver.getmsgs()
            for msg in msgs:
                

                if str(msg['message_create']['sender_id']) == str(ctrls.dm_rec_id):
                    continue
                
                current_time =datetime.fromtimestamp(int(msg['created_timestamp']) / 1000)#utils.convert_timestamp(int(msg['created_timestamp']) / 1000)
                elapsed_sec = (current_time - start_time).total_seconds()

                print(msg['message_create']['message_data']['text'])

                text = msg['message_create']['message_data']['text']
                user_id_str = str(msg['message_create']['sender_id'])
    

                screenname = ""
                if ctrls.getuser(user_id_str) == None:
                    screenname =  utils.absolutedofunc(ctrls.twapi.get_user, user_id = int(user_id_str)).screen_name

                utils.setdefaultuser(ctrls, user_id_str, screenname)

                ctrls.db['user'].update_one({'user_id' : user_id_str}, {'$addToSet' : {'history': problem_num}})

                if user_id_str not in user_got_score.keys():
                    user_got_score[user_id_str] = 0

                ways = utils.parsetext(text, ctrls.getuser(user_id_str)['keyconfig'])



                if ways != -1:
                    waycou = utils.checkanswer(mp,robotpos,goalpos,mainrobot, ways)
                    if waycou != -1:
                        
                        point = max(1, int((point_rate[0] * (problem_length - elapsed_sec) + point_rate[1] * elapsed_sec) / problem_length * math.pow(0.5, waycou - optimal_moves)))
                        user_got_score[user_id_str] = max(point , user_got_score[user_id_str])
                        ctrls.dmapi.send_dm(user_id_str, "Accepted!(" + str(waycou) + "moves " + str(elapsed_sec) + "sec " + str(point) + "pt).\nYour current score is " + str(user_got_score[user_id_str]) + "pt")
                        

                #    else:
                #        ctrls.dmapi.send_dm(user_id_str, "Wrong Answer.")
                #else:
                #    ctrls.dmapi.send_dm(user_id_str, "Invalid format.")


        if (datetime.now() - start_time).total_seconds() >= problem_length:
            break;
            
        utils.sleepwithlisten(ctrls, 1, roundstart)

        
    for key in user_got_score.keys():
        ctrls.db['user'].update({'user_id':key}, {'$inc' : {'roundscore': user_got_score[key]}})
        ctrls.db['user'].update({'user_id':key}, {'$inc' : {'pointsum.Time-Limited': user_got_score[key]}})
        
    tweetproblemresult(ctrls, curproblemid, problem_num, user_got_score)

    #checksubmissions(ctrls, problemstart_timestamp, curproblemid, problem_num)
    
    webhook_receiver.stop(ctrls)

    return
