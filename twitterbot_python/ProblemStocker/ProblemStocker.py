import ProblemGenerator
import pymongo
import string
import random
mongocl = pymongo.MongoClient('localhost', 27017)
print('input mode = [test:0, real:1]')
istest = int(input())
print('timeout:')
timeout = int(input())
if istest == 1:
    db = mongocl['ricochetrobots']
if istest == 0:
    db = mongocl['ricochettest']

while True:
    db['problem'].save(ProblemGenerator.ProblemGenerate(0, timeout,random.randint(0,2)>0,random.randint(0,2)>0))
