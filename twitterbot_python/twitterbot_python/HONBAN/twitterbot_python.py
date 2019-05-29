import tweepy
import time
import utils
import json
import wankosobaround
import directmessage
import timelimitround
from datetime import datetime

CONSUMER_KEY = 'kNePGOncpjWFreJ328eyYohGz'
CONSUMER_SECRET = 'UT1iFpefTYbGfP2xL5hjGCYQnqNUku0XN3MA4Oi14nnc15WI5I'
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

#redirect_url = auth.get_authorization_url()

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
api = tweepy.API(auth, wait_on_rate_limit=True)

dmapi = directmessage.DirectMessanger(CONSUMER_KEY,CONSUMER_SECRET,ACCESS_TOKEN,ACCESS_SECRET)

print('Done!')

utils.getmentions.lastgettime = datetime(2000,10,1,0,0,0,0)
utils.getmentions.lastid = api.mentions_timeline(count=1)[0].id


roundrange = [5,55]

with open('userdata.json') as f:
    userdata = json.load(f)
    while datetime.now().minute < roundrange[0] or datetime.now().minute >= roundrange[1]:
        utils.sleepwithlisten(api,1, userdata)

roundstart = None
timelimit = None
roundname = str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour)

with open('rounds.json') as f:
    rounds = json.load(f)

if roundname in rounds.keys():
    roundstart = rounds[roundname]['roundstart']
    timelimit = datetime.strptime(rounds[roundname]['timelimit'], '%Y/%m/%d %H:%M:%S')

while True:
    
    if roundstart == None:
        utils.absolutedofunc(api.update_status,'Round ' + str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour))

    curproblemid, problemname = wankosobaround.tweetnewproblem(api)

    if roundstart == None:
        roundstart = int(problemname)
        roundname = str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour)
        timelimit = datetime.now()
        timelimit = datetime(timelimit.year, timelimit.month, timelimit.day, timelimit.hour, roundrange[1], 0, 0)
        
        with open('rounds.json', 'w') as f:
            rounds[roundname] = {}
            rounds[roundname]['roundstart'] = roundstart
            rounds[roundname]['timelimit'] = timelimit.strftime('%Y/%m/%d %H:%M:%S')
            json.dump(rounds,f)

    wankosobaround.wankoround(api, timelimit, roundstart, curproblemid, problemname)
    
    with open('userdata.json') as f:
        userdata = json.load(f)
        if datetime.now() >= timelimit:
        
            utils.tweetoverallranking(api, userdata, reply_id = utils.tweethourlyranking(api, userdata, roundstart, basetext = 'Round ' + roundname + ' Finished\n').id)
            roundstart = None
        
            utils.sleepwithlisten(api,600, userdata)
        else:
            utils.sleepwithlisten(api,20, userdata, roundstart)