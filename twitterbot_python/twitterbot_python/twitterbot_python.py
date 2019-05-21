import tweepy
import time

CONSUMER_KEY = 'kNePGOncpjWFreJ328eyYohGz'
CONSUMER_SECRET = 'UT1iFpefTYbGfP2xL5hjGCYQnqNUku0XN3MA4Oi14nnc15WI5I'
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

redirect_url = auth.get_authorization_url()


print('Get your verification code from: ' + redirect_url)

verifier = input('Type the verification code: ').strip()

auth.get_access_token(verifier)
ACCESS_TOKEN = auth.access_token
ACCESS_SECRET = auth.access_token_secret

auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

api = tweepy.API(auth)

print('Done!')

lastid = api.mentions_timeline(count=1)[0].id

while True:
    mentions = api.mentions_timeline(since_id=lastid)
    if len(mentions) > 0:
        lastid = mentions[0].id
        for stat in mentions:
            print(stat.text)
            api.update_status("thank you for replying", in_reply_to_status_id=stat.id, auto_populate_reply_metadata=True)
    time.sleep(15)

stat = api.update_status('tweet from python');
stat