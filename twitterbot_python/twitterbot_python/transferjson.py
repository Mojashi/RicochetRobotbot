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
print('input mode = [test:0, real:1]')

istest = int(input())
if istest == 1:
    db = mongocl['ricochetrobots']
if istest == 0:
    db = mongocl['ricochettest']

data = []

with open('userdata.json') as f:
    dict = json.load(f)
    for item in dict.items():
        for i in range(len(item[1]['history'])):
            item[1]['history'][i] = int(item[1]['history'][i])


        item[1].pop('winhistory')

        buf = {'user_id':item[0], 'pointsum':{'Wanko-Soba':item[1]['wincount'], 'Time-Limited':0}}
        buf.update(item[1])
        data.append(buf)

    result = db['user'].insert(data)
    print(result)
    
data = []
with open('history.json') as f:
    dict = json.load(f)
    for item in dict.items():
        buf = {'problem_num':int(item[0]), 'used' : True,'tweet_id':item[1]}
        with open('problems/' + str(item[0]) + '.json') as fp:
            dic = json.load(fp)
            dic.update({'optimal_moves':int(dic['answer'][0])})
            dic['answer'].pop()
            buf.update(dic)

        data.append(buf)

    result = db['problem'].insert(data)
    print(result)
    
data = []
with open('rounds.json') as f:
    dict = json.load(f)
    for item in dict.items():
        buf = {'round_num':item[0]}
        buf.update(item[1])

        data.append(buf)

    result = db['round'].insert(data)
    print(result)