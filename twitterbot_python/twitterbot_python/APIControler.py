import tweepy
import time
import msvcrt
import traceback
import sys
import copy
import random
import re
from PIL import Image
from datetime import datetime
from imgurpython import ImgurClient
import pymongo
import utils
from requests_oauthlib import OAuth1Session
import directmessage

class APIControler:
    def __init__(self):
        CONSUMER_KEY = 'kNePGOncpjWFreJ328eyYohGz'
        CONSUMER_SECRET = 'UT1iFpefTYbGfP2xL5hjGCYQnqNUku0XN3MA4Oi14nnc15WI5I'
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        
        #redirect_url = auth.get_authorization_url()
        
        #print('Get your verification code from: ' + redirect_url)
        
        #verifier = input('Type the verification code: ').strip()
        
        #auth.get_access_token(verifier)
        print('input mode = [test:0, real:1]')
        
        istest = int(input())

        if istest == 0:
            ACCESS_TOKEN = '1131066930478034944-dOEypEJR06qTos6usCQpvAqIgirZS8'
            ACCESS_SECRET = 'etEIzdmzHi99aTcgfkWmwmhEkDRbdT6r4FAc0lsaZYkmW'
            self.dm_rec_id = 1131066930478034944
        else:
            ACCESS_TOKEN = '1117739551873568768-P7YUwZGNXQJ8Y7simuiGz91RjcJ42l'
            ACCESS_SECRET = 'bwqv9RLTVJcS0VN77RazaHKaqSXB5WYTUAbiy5ERrTZ4b'
            self.dm_rec_id = 1117739551873568768
        
        auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
        self.twapi = tweepy.API(auth, wait_on_rate_limit=True)
        
        
        self.oauth_twitter = OAuth1Session(self.CONSUMER_KEY, self.CONSUMER_SECRET,self.ACCESS_TOKEN,self.ACCESS_SECRET)
        
        self.dmapi = directmessage.DirectMessanger(self.oauth_twitter)


        print('Done!')

        self.mongocl = pymongo.MongoClient('localhost', 27017)
        
        if istest == 0:
            self.db = self.mongocl['ricochettest']
        else:
            self.db = self.mongocl['ricochetrobots']

        utils.setdefaultcollection(self)

    
    def getuser(self,user_id_str):
        return self.db['user'].find_one({'user_id' : user_id_str})
    