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
from imgurpython import ImgurClient
import pymongo
import json


mongocl = pymongo.MongoClient('localhost', 27017)
db = mongocl['ricochettest']
data = []

#with open('userdata.json') as f:
#    dict = json.load(f)
#    for item in dict.items():
#        for i in len(item[1]['history']):
#            item[1][i] = int(item[1]['history'][i])
#        buf = {'user_id':item[0]}
#        buf.update(item[1])
#        data.append(buf)

#    result = db['user'].insert(data)
#    print(result)

#with open('history.json') as f:
#    dict = json.load(f)
#    for item in dict.items():
#        buf = {'problem_num':int(item[0]), 'tweet_id':item[1]}
#        with open('problems/' + str(item[0]) + '.json') as fp:
#            dic = json.load(fp)
#            dic.update({'optimal_moves':int(dic['answer'][0])})
#            dic['answer'].pop()
#            buf.update(dic)

#        data.append(buf)

#    result = db['problem'].insert(data)
#    print(result)

with open('rounds.json') as f:
    dict = json.load(f)
    for item in dict.items():
        buf = {'round_num':item[0]}
        buf.update(item[1])

        data.append(buf)

    result = db['round'].insert(data)
    print(result)