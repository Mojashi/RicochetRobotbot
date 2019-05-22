import tweepy
import time
import subprocess
import json
import copy
import ProblemGenerator

def checkanswer(mp, robotpos, goalpos, mainrobot, ans):
    Dirnum = {'u':0,'r':1, 'd':2,'l':3}
    Dir = [[0,-1],[1,0],[0,1],[-1,0]]
    curpos = copy.copy(robotpos)

    ways =ans.split()

    while ways[0][0] == '@':
        ways.pop(0)

    for way in ways[0].split(','):
        if len(way) != 2:
            return -1
        if not(ord(way[0])>=ord('0') and ord(way[0]) <= ord('4')):
            return -1
        if way[1] !='u' and way[1] !='r' and way[1] !='d' and way[1] !='l':
            return -1

        num = int(way[0])
        d = Dirnum[way[1]]

        while True:
            nex = [curpos[num][0] + Dir[d][0],curpos[num][1] + Dir[d][1]]
            if mp[curpos[num][0]][curpos[num][1]][d] == 1 or nex in curpos:
                break
            curpos[num] = nex

    if curpos[mainrobot] != goalpos:
        return -1

    return len(ways[0].split(','))

def tweetnewproblem():
    
    with open('history.json','r') as f:
        history = json.load(f)

    ProblemGenerator.ProblemGenerate('problems/' + str(len(history) + 1))
    
    stat = api.update_with_media(filename='problems/'+str(len(history) + 1)+'.png', status="Problem number:"+str(len(history) + 1))

    history[len(history) + 1] = stat.id

    with open('history.json','w') as f:
        json.dump(history, f)

    return stat.id, str(len(history))

def maincycle():

    curshortest = 10000000
    curproblemid, problemname = tweetnewproblem()
    lastid = curproblemid
    
    with open('problems/'+problemname+'.json') as f:
        cdict = json.load(f)
        mp = cdict['board']
        robotpos = cdict['robotpos']
        goalpos = cdict['goalpos']
        mainrobot = cdict['mainrobot']
        answer =  cdict['answer']

    while True:
        mentions = api.mentions_timeline(since_id=lastid)
        if len(mentions) > 0:
            lastid = mentions[0].id
            mentions.reverse()
            for stat in mentions:
                if stat.in_reply_to_status_id != curproblemid:
                    continue
                print("from:"+stat.user.screen_name + " " + stat.text)
                waycou = checkanswer(mp,robotpos,goalpos,mainrobot,stat.text)

                if waycou == -1:
                    text = "Wrong Answer"
                else:
                    text = "Accepted"
                    if curshortest > waycou:
                        curshortest = waycou
                        text += '\nCurrently Shortest'
                    if int(answer[0]) == waycou:
                        text += '\nOptimal'
                    
                api.update_status(text, in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
                
                if int(answer[0]) == waycou:
                    api.update_status('Finished.\nWinner @'+stat.user.screen_name, in_reply_to_status_id=curproblemid, auto_populate_reply_metadata=True)
                    return

        time.sleep(15)
        


CONSUMER_KEY = 'kNePGOncpjWFreJ328eyYohGz'
CONSUMER_SECRET = 'UT1iFpefTYbGfP2xL5hjGCYQnqNUku0XN3MA4Oi14nnc15WI5I'
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

redirect_url = auth.get_authorization_url()


#print('Get your verification code from: ' + redirect_url)

#verifier = input('Type the verification code: ').strip()

#auth.get_access_token(verifier)
ACCESS_TOKEN = '1117739551873568768-P7YUwZGNXQJ8Y7simuiGz91RjcJ42l'
ACCESS_SECRET = 'bwqv9RLTVJcS0VN77RazaHKaqSXB5WYTUAbiy5ERrTZ4b'

auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

api = tweepy.API(auth)

print('Done!')

while True:
        maincycle()
    