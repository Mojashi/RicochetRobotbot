import tweepy
import datetime

def gettwitterdata(keyword,dfile):

    Consumer_key = 'kNePGOncpjWFreJ328eyYohGz'
    Consumer_secret = 'UT1iFpefTYbGfP2xL5hjGCYQnqNUku0XN3MA4Oi14nnc15WI5I'
    Access_token = '953817124748738561-fPoMGgUygN8nIoHAGIiXdu6TAn9eJBd'
    Access_secret = 'XVHphf6VFbXFglpmUom59Vg70FVco7Kpp2R6BTPtS5Ida'

    auth = tweepy.OAuthHandler(Consumer_key, Consumer_secret)
    auth.set_access_token(Access_token, Access_secret)

    api = tweepy.API(auth, wait_on_rate_limit = True)

    q = keyword

    tweets_data =[]

    for tweet in tweepy.Cursor(api.search, q=q, count=100,tweet_mode='extended').items():

        tweets_data.append(tweet.full_text + '\n')


    fname = r"'"+ dfile + "'"
    fname = fname.replace("'","")

    with open(fname, "w",encoding="utf-8") as f:
        f.writelines(tweets_data)


if __name__ == '__main__':

    print ('====== Enter Serch KeyWord   =====')
    keyword = input('>  ')

    print ('====== Enter Tweet Data file =====')
    dfile = input('>  ')

    gettwitterdata(keyword,dfile)