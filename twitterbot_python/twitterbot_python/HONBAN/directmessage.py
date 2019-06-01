import requests
import json
from requests_oauthlib import OAuth1Session
import os
import sys
import time

class DirectMessanger:
    class BadRequest(Exception):
        pass

    def __init__(self, consumer_key,consumer_secret, access_token,access_token_secret):
        self.twitter = OAuth1Session(consumer_key, consumer_secret, access_token, access_token_secret)
        self.headers = {"content-type": "application/json"}

    def receive_dm(self, since_timestamp=-1, until_timestamp=-1, count=20000000):
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
                print('dm send error')
                sleep(600)
                continue
            
            if 'next_cursor' not in jsn.keys():
                jsn['next_cursor'] = 0

            cursor = jsn['next_cursor']

            if len(jsn['events']) == 0:
                break

            for msg in jsn['events']:
                if int(msg['created_timestamp']) >= int(until_timestamp):
                    continue

                if int(msg['created_timestamp']) <= int(since_timestamp) or len(msgs) >= count:
                    cursor = 0
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
        return jsn['event']['created_timestamp']


    

    def uploadmedia(self, filename):
        self.video_filename = filename
        self.total_bytes = os.path.getsize(self.video_filename)
        self.media_id = None
        self.processing_info = None
        
        self.upload_init()
        self.upload_append()
        self.upload_finalize()

        return self.media_id

    def upload_init(self):
        '''
        Initializes Upload
        '''
        print('INIT')

        request_data = {
            'command': 'INIT',
            'media_type': 'image/gif',
            'total_bytes': self.total_bytes,
            'media_category': 'tweet_gif'
        }

        req = self.twitter.post(url='https://upload.twitter.com/1.1/media/upload.json', data=request_data)
        media_id = req.json()['media_id']

        self.media_id = media_id

        print('Media ID: %s' % str(media_id))


    def upload_append(self):
        '''
        Uploads media in chunks and appends to chunks uploaded
        '''
        segment_id = 0
        bytes_sent = 0
        file = open(self.video_filename, 'rb')

        while bytes_sent < self.total_bytes:
            chunk = file.read(4 * 1024 * 1024)
            
            print('APPEND')

            request_data = {
                'command': 'APPEND',
                'media_id': self.media_id,
                'segment_index': segment_id
            }

            files = {
                'media':chunk
            }

            req = self.twitter.post(url='https://upload.twitter.com/1.1/media/upload.json', data=request_data, files=files)

            if req.status_code < 200 or req.status_code > 299:
                print(req.status_code)
                print(req.text)
                sys.exit(0)

            segment_id = segment_id + 1
            bytes_sent = file.tell()

            print('%s of %s bytes uploaded' % (str(bytes_sent), str(self.total_bytes)))

        print('Upload chunks complete.')


    def upload_finalize(self):
        '''
        Finalizes uploads and starts video processing
        '''
        print('FINALIZE')

        request_data = {
            'command': 'FINALIZE',
            'media_id': self.media_id
        }

        req = self.twitter.post(url='https://upload.twitter.com/1.1/media/upload.json', data=request_data)
        print(req.json())

        self.processing_info = req.json().get('processing_info', None)
        self.check_status()


    def check_status(self):
        '''
        Checks video processing status
        '''
        if self.processing_info is None:
            return

        state = self.processing_info['state']

        print('Media processing status is %s ' % state)

        if state == u'succeeded':
            return

        if state == u'failed':
            sys.exit(0)

        check_after_secs = self.processing_info['check_after_secs']
        
        print('Checking after %s seconds' % str(check_after_secs))
        time.sleep(check_after_secs)

        print('STATUS')

        request_params = {
            'command': 'STATUS',
            'media_id': self.media_id
        }

        req = self.twitter.get(url='https://api.twitter.com/1.1/statuses/update.json', params=request_params)
        
        self.processing_info = req.json().get('processing_info', None)
        self.check_status()


