import requests
import json
from requests_oauthlib import OAuth1Session


class DirectMessanger:
    class BadRequest(Exception):
        pass

    def __init__(self, consumer_key,consumer_secret, access_token,access_token_secret):
        self.twitter = OAuth1Session(consumer_key, consumer_secret, access_token, access_token_secret)
        self.headers = {"content-type": "application/json"}

    def receive_dm(self, since_timestamp = -1, count = 20):
        url = "https://api.twitter.com/1.1/direct_messages/events/list.json?count=50"
        cursor = -1
        msgs = []

        while len(msgs) < count and cursor != 0:
            realurl = url
            if cursor != -1:
                realurl += '&cursor=' + str(cursor)

            ret_json = self.twitter.get(realurl, headers = self.headers)
            jsn = json.loads(ret_json.text)

            if ret_json.status_code != 200:
                raise self.BadRequest()
            
            if 'next_cursor' not in jsn.keys():
                jsn['next_cursor'] = 0

            cursor = jsn['next_cursor']

            if len(jsn['events']) == 0:
                break

            for msg in jsn['events']:
                if int(msg['created_timestamp']) <= since_timestamp or len(msgs) >= count:
                    break
                msgs.append(msg)
            

        return msgs

    def send_dm(self, target_id, msg_text):
        url = "https://api.twitter.com/1.1/direct_messages/events/new.json"
        param = {"event": {"type": "message_create", "message_create": {"target": {"recipient_id": target_id}, "message_data": {"text": msg_text}}}}
        ret = self.twitter.post(url, headers = self.headers, data = json.dumps(param))
        if ret.status_code != 200:
                raise self.BadRequest()

        jsn = json.loads(ret.text)
        return jsn['event']['id']