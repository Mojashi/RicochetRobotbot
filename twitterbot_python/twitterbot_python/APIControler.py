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
from oauth2client.service_account import ServiceAccountCredentials
from httplib2 import Http
import gspread


class APIControler:
    def __init__(self):
        self.CONSUMER_KEY = 'kNePGOncpjWFreJ328eyYohGz'
        self.CONSUMER_SECRET = 'UT1iFpefTYbGfP2xL5hjGCYQnqNUku0XN3MA4Oi14nnc15WI5I'
        auth = tweepy.OAuthHandler(self.CONSUMER_KEY, self.CONSUMER_SECRET)
        
        #redirect_url = auth.get_authorization_url()
        
        #print('Get your verification code from: ' + redirect_url)
        
        #verifier = input('Type the verification code: ').strip()
        
        #auth.get_access_token(verifier)
        print('input mode = [test:0, real:1]')
        
        istest = int(input())

        if istest == 0:
            self.ACCESS_TOKEN = '1131066930478034944-dOEypEJR06qTos6usCQpvAqIgirZS8'
            self.ACCESS_SECRET = 'etEIzdmzHi99aTcgfkWmwmhEkDRbdT6r4FAc0lsaZYkmW'
            self.dm_rec_id = 1131066930478034944
        else:
            self.ACCESS_TOKEN = '1117739551873568768-P7YUwZGNXQJ8Y7simuiGz91RjcJ42l'
            self.ACCESS_SECRET = 'bwqv9RLTVJcS0VN77RazaHKaqSXB5WYTUAbiy5ERrTZ4b'
            self.dm_rec_id = 1117739551873568768
        
        auth.set_access_token(self.ACCESS_TOKEN, self.ACCESS_SECRET)
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

        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        json_file = 'My Project-bec28df6f14f.json'#OAuth用クライアントIDの作成でダウンロードしたjsonファイル
        credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file, scopes=scopes)
        http_auth = credentials.authorize(Http())
        
        # スプレッドシート用クライアントの準備
        self.doc_id = '1blK7Tkf5tTK1OfaUdwOkYU-nDB6XWkwwy5ZODgA8sTs'#これはスプレッドシートのURLのうちhttps://docs.google.com/spreadsheets/d/以下の部分です
        self.gclient = gspread.authorize(credentials)
        self.gfile   = self.gclient.open_by_key(self.doc_id)#読み書きするgoogle spreadsheet
        self.worksheet  = self.gfile.sheet1
    
    def getuser(self,user_id_str):
        return self.db['user'].find_one({'user_id' : user_id_str})
    