import webhook_receiver
import time
import multiprocessing
import utils    
import json
import random
import os
import math
from datetime import datetime

contest_problem_num = 3

def tweetcontestresult(ctrls, user_got_scores, contest_num):
    
    text = 'RicochetRobotsContest' + str(contest_num) +' Result:\n\n'

    scoresum = {}
    
    for item in user_got_scores.items():
        for i in range(contest_problem_num):
            if item[0] not in scoresum.keys():
                scoresum[item[0]] = 0
            scoresum[item[0]] += item[1][i]

    sortedscore = sorted(scoresum.items(), key=lambda x:x[1],reverse=True)

    rank = 1
    bef = -1
    cou = 1

    for po in sortedscore:
        if bef != po[1]:
            rank = cou
        text +=str(rank) + '. ' + utils.decoratename(ctrls, po[0], '@'+ctrls.getuser(po[0])['screen_name']) + ' ' + str(po[1]) + 'pt\n'
        cou += 1
        bef = po[1]

    utils.tweetlongtext(ctrls, status = text)
    
    return

def update_rating(ctrls, user_got_scores):
    ratedrankmemo = {}
    
    def getRatedRank(X):
        if X in ratedrankmemo.keys():
            return ratedrankmemo[X]
        sum = 0
        for item in user_got_scores.items():
            sum += 1.0 / (1.0 + math.pow(6.0, ((X - ctrls.getuser(item[0])['inner_rating']) / 400.0)))
        ratedrankmemo[X] = sum
        return sum

    def inner_perf(x):
        
        upper = 6144
        lower = -2048
        while upper - lower > 0.5:
            mid = (upper + lower) / 2
            if x - 0.5 > getRatedRank(mid):
                upper = mid
            else:
                lower = mid
        
        return int((upper + lower) / 2);
    
    scoresum = {}
    
    for item in user_got_scores.items():
        for i in range(contest_problem_num):
            if item[0] not in scoresum:
                scoresum[item[0]] = 0
            scoresum[item[0]] += item[1][i]

    sortedscore = sorted(scoresum.items(), key=lambda x:x[1],reverse=True)
    
    cnt = 1
    rank = 0
    bef = -1
    for usr in sortedscore:
        if bef != usr[1]:
            rank = cnt

        perf = inner_perf(rank)
        ctrls.db['user'].update_one({'user_id' : usr[0]}, {'$addToSet' : {'performance_history': perf}})

        bef = usr[1]
        cnt+=1

    for item in user_got_scores.items():
        perf_his = ctrls.getuser(item[0])['performance_history']
        perf_his.reverse()
        rating = 0
        partc = len(perf_his)

        inner_rating = 0
        bosum = 0
        for i in range(partc):
            inner_rating += math.pow(0.9, i + 1) * perf_his[i]
            bosum += math.pow(0.9, i + 1)
        inner_rating /= bosum


        for i in range(partc):
            rating += math.pow(2.0, perf_his[i]/800.0) * math.pow(0.9, i + 1)

        rating = 800 * math.log2(rating / bosum)
        rating = rating - 1200 * (math.sqrt(1 - math.pow(0.81, partc)) / (1 - math.pow(0.9, partc)) - 1) / (math.sqrt(19.0) - 1)
        
        if rating <= 400:
            rating = math.exp(400 / ((400 - rating) / 400))
            
        ctrls.db['user'].update_one({'user_id' : item[0]}, {'$set' : {'inner_rating' : rating}})
        ctrls.db['user'].update_one({'user_id' : item[0]}, {'$set' : {'rating' : rating}})

def update_ranking(ctrls, user_got_scores):
    scoresum = {}
    
    for item in user_got_scores.items():
        for i in range(contest_problem_num):
            if item[0] not in scoresum:
                scoresum[item[0]] = 0
            scoresum[item[0]] += item[1][i]

    table = {}

    for i in range(1000):
        table[i]= {}
        for j in range(100):
            table[i][j] = ''

    sortedscore = sorted(scoresum.items(), key=lambda x:x[1],reverse=True)

    
    cell_list = ctrls.worksheet.range('A1:M' + str(1 + len(user_got_scores.keys())))
    
    cnt = 1
    rank = 0
    bef = -1
    for usr in sortedscore:
        if bef != usr[1]:
            rank = cnt
        table[cnt + 1][1] = rank
        table[cnt + 1][2] = ctrls.getuser(usr[0])['screen_name']
        table[cnt + 1][3] = usr[1]
        for i in range(contest_problem_num):
            table[cnt + 1][4 + i] = user_got_scores[usr[0]][i]

        bef = usr[1]
        cnt+=1
        

    table[1][1] = len(user_got_scores.keys())
    table[1][2] = contest_problem_num

    for cell in cell_list:
        cell.value = str(table[cell.row][cell.col])

    ctrls.worksheet.update_cells(cell_list)



def tweetnewproblem(ctrls, move, num):
    
    #movecount = ProblemGenerator.ProblemGenerate('problems/' + str(len(history) + 1), 8)
    
    
    newprob = None
    while newprob == None:
        newprob = utils.picknewproblem(ctrls, move)


    stat = utils.absolutedofunc(ctrls.twapi.update_with_media, filename=newprob['img'],
                               status="この問題の回答はリプライではなくDMで送信してください。解答の冒頭に " + str(num) + ": と付けてください。\nProblem number:" + str(newprob['problem_num']) + "\nOptimal:" +str(newprob['optimal_moves']) + 'moves\nhttps://twitter.com/messages/compose?recipient_id='+str(ctrls.dm_rec_id))
    
    newprob['tweet_id'] = stat.id
    ctrls.db['problem'].save(newprob)

    return stat.id, newprob['problem_num']


def startround(ctrls, roundstart, timelimit, roundname):
    

    contest_num = 1 + len(list(ctrls.db['round'].find({'mode':'Contest'})))
    

    maincycle(ctrls,  contest_num)

    os.remove('contest_temp.json')

    utils.sleepwithlisten(ctrls, (timelimit - datetime.now()).total_seconds(), roundstart)

    return



def maincycle(ctrls, contest_num):

    problem_ids = []
    problem_nums = []
    move_range = [[3,5], [3,5], [6,8], [6,8], [9,15],[9,15], [9,15], [9,15], [9,15],[9,15]]#[[3,5], [3,5], [6,8], [6,8], [9,15],[9,15], [9,15], [9,15], [16,18], [19,100]]
    
    cdicts = []
    user_got_scores = {}
    assumed_solutions = []

    timelimit = 30

    point_rate = [100, 60]
    
    start_time = datetime.now()


    if os.path.exists('contest_temp.json'):
        with open('contest_temp.json') as f:
            jsnn = json.load(f)
            problem_nums = jsnn['problem_nums']
            problem_ids = jsnn['problem_ids']
            user_got_scores = jsnn['user_got_scores']
            start_time = datetime.strptime(jsnn['start_time'], '%Y/%m/%d %H:%M:%S')

    else:
        with open('contest_temp.json', 'w') as f:
            f.write('')
        for i in range(contest_problem_num):
            id,num = tweetnewproblem(ctrls, random.randint(move_range[i][0],move_range[i][1]), i)
            problem_ids.append(id)
            problem_nums.append(num)


    for i in range(contest_problem_num):
        cdicts.append(ctrls.db['problem'].find_one({'problem_num':problem_nums[i]}))
        assumed_solutions.append(utils.convertans(cdicts[i]['answer'], cdicts[i]['robotpos']))
        print(assumed_solutions[i])

    #utils.sleepwithlisten(api, min(5 * 60, (timelimit - datetime.now()).total_seconds()), roundstart)
    #utils.sleepwithlisten(ctrls, 5 * 60, roundstart)
    
    que = webhook_receiver.start(ctrls)

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
    
                
                try:
                    pnum = int(text.split(':')[0])
                except ValueError:
                    continue

                if pnum < 0 or pnum >= contest_problem_num:
                    continue

                mp = cdicts[pnum]['board']
                robotpos = cdicts[pnum]['robotpos']
                goalpos = cdicts[pnum]['goalpos']
                mainrobot = cdicts[pnum]['mainrobot']
                answer = cdicts[pnum]['answer']
                imgname = cdicts[pnum]['img']
                baseimgname = cdicts[pnum]['baseimg']
                optimal_moves = cdicts[pnum]['optimal_moves']

                screenname = ""
                if ctrls.getuser(user_id_str) == None:
                    screenname =  utils.absolutedofunc(ctrls.twapi.get_user, user_id = int(user_id_str)).screen_name

                utils.setdefaultuser(ctrls, user_id_str, screenname)
                
                ctrls.db['user'].update_one({'user_id' : user_id_str}, {'$addToSet' : {'contest_history': contest_num}})

                ctrls.db['user'].update_one({'user_id' : user_id_str}, {'$addToSet' : {'history': problem_nums[pnum]}})

                if user_id_str not in user_got_scores.keys():
                    user_got_scores[user_id_str] = [0,0,0,0,0,0,0,0,0,0]

                ways = utils.parsetext(text.split(':')[1], ctrls.getuser(user_id_str)['keyconfig'])


                if ways != -1:
                    waycou = utils.checkanswer(mp,robotpos,goalpos,mainrobot, ways)
                    if waycou != -1:
                        
                        point = max(1, int((point_rate[0] * (timelimit - elapsed_sec) + point_rate[1] * elapsed_sec) / timelimit * math.pow(0.5, waycou - optimal_moves)))
                        user_got_scores[user_id_str][pnum] = max(point , user_got_scores[user_id_str][pnum])
                        ctrls.dmapi.send_dm(user_id_str, "Accepted!(" + str(waycou) + "moves " + str(elapsed_sec) + "sec " + str(point) + "pt).\nYour current score is " + str(user_got_scores[user_id_str][pnum]) + "pt")
                        

                    else:
                        ctrls.dmapi.send_dm(user_id_str, "Wrong Answer.")
                else:
                    ctrls.dmapi.send_dm(user_id_str, "Invalid format.")
                    
        with open('contest_temp.json', 'w') as f:
            json.dump({'user_got_scores' : user_got_scores, 'start_time':start_time.strftime('%Y/%m/%d %H:%M:%S'), 'problem_nums' : problem_nums, 'problem_ids':problem_ids},f)

        update_ranking(ctrls,user_got_scores)

        if (datetime.now() - start_time).total_seconds() >= timelimit:
            break;
        
        

        utils.sleepwithlisten(ctrls, 1)

        
    for key in user_got_scores.keys():
        for i in range(contest_problem_num):
            ctrls.db['user'].update({'user_id':key}, {'$inc' : {'roundscore': user_got_scores[key][i]}})
        
    update_rating(ctrls, user_got_scores)
    tweetcontestresult(ctrls,user_got_scores,contest_num)
    #checksubmissions(ctrls, problemstart_timestamp, curproblemid, problem_num)
    
    webhook_receiver.stop(ctrls)

    return
