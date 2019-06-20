import time
import threading
from flask import Flask, request
import base64
import hashlib
import hmac
import copy
import json
import urllib.parse
from requests_oauthlib import OAuth1Session
import requests
import APIControler
import twitterbot_python
import queue
import ssl

app = Flask(__name__)

env_name = "mojashidev"
webhook_id = None
ctrls = None
que = queue.Queue()


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    print(request.data)
    if request.data == b'asdiasjdasjddjjsaiioadsiojdosaidjasiod':
        shutdown_server()
    return 'Server shutting down...'


@app.route('/.well-known/acme-challenge/GA5LMZyE3ZRmkugjZneTxb5aZCHH4645k6oKhD9Hg0A', methods = ['GET'])
def validcheck():
   
    return 'GA5LMZyE3ZRmkugjZneTxb5aZCHH4645k6oKhD9Hg0A.vxOGVPt2v_GkQ3TLSxaxf7XyVCUVJchkEzdhj-KzvQI', 200, {'Content-Type': 'text/plain'}

@app.route('/index.html', methods = ['GET'])
def getpage():
   
    return 'Hello World', 200, {'Content-Type': 'text/plain'}


@app.route('/webhook/twitter', methods = ['GET'])
def get_crc():
    global ctrls
    if 'crc_token' in request.args and len(request.args.get('crc_token')) == 48:
        crc_token = request.args.get('crc_token')
        sha256_hash_digest = hmac.new(ctrls.CONSUMER_SECRET.encode(), msg = crc_token.encode(), digestmod = hashlib.sha256).digest()

        response_token = 'sha256=' + base64.b64encode(sha256_hash_digest).decode()
        response = {'response_token': response_token}

        return json.dumps(response), 200, {'Content-Type': 'application/json'}

    return 'No Content', 204, {'Content-Type': 'text/plain'}

@app.route('/webhook/twitter',methods=['POST'])
def index():
    global que
    if request.headers['Content-Type'] == 'application/json':
        if "direct_message_events" in request.json.keys():
            que.put(request.json)
            print('DM')
    return "OK"

    #app.run(debug=False, host="0.0.0.0", port = 80)

server = None
running = False


def getmsgs():
    global que
    msgs = []


    while que.empty() == False:
        print('get')
        msgs.extend(que.get()["direct_message_events"])
    print('empty')
    return msgs

def subscribe(ctrls):
    global webhook_id
    my_url = 'https://ricochetrobots.mojashidev.xyz/webhook/twitter'
    sub_url = "https://api.twitter.com/1.1/account_activity/all/" + env_name + "/webhooks.json?url=" +urllib.parse.quote(my_url,safe='')

    
    #req = ctrls.oauth_twitter.post(url=sub_url)

    #if req.status_code == 200:
    #    print ("subscribed")
    #else:
    #    print(req)
    #    print("subscribe failed")
    #    #return

    webhook_id = ctrls.oauth_twitter.get(url = 'https://api.twitter.com/1.1/account_activity/all/webhooks.json').json()["environments"][0]['webhooks'][0]['id']
    
    unsub_url = "https://api.twitter.com/1.1/account_activity/all/"+env_name+"/webhooks/"+ str(webhook_id) + ".json"
    
    req = ctrls.oauth_twitter.put(url = unsub_url)
    print('subed')
    #sub_url  ="https://api.twitter.com/1.1/account_activity/all/" + env_name + "/subscriptions.json"
    #req = ctrls.oauth_twitter.post(url = sub_url)

    return 

def unsubscribe(ctrls):
    global webhook_id

    unsub_url = "https://api.twitter.com/1.1/account_activity/all/"+env_name+"/subscriptions.json"

    ctrls.oauth_twitter.delete(url = unsub_url)

    unsub_url = "https://api.twitter.com/1.1/account_activity/all/"+env_name+"/webhooks/"+ str(webhook_id) + ".json"
    
    ctrls.oauth_twitter.delete(url = unsub_url)

    return


def run(que_al, ctrls_al):
    global ctrl
    global que
    ctrl = ctrls_al
    que = que_al
    print("start hook")
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.load_cert_chain(
        'openssl/fullchain.pem', 'openssl/privkey.pem'
    )
    app.run(host='0.0.0.0', port=443, ssl_context=ssl_context, threaded=False, debug=False)
    return

def start(ctrls_al):
    global running
    global server
    global que
    global ctrls
    ctrls = ctrls_al
    if running == True:
        return que

    running = True

    server = threading.Thread(target=run, kwargs={'que_al':que,'ctrls_al':ctrls_al})
    server.start()

    time.sleep(7)
    
    subscribe(ctrls_al)

    return que


def stop(ctrls):
    global running
    global server

    if running == False:
        return

    running = False

    #unsubscribe(ctrls)

    requests.post('https://ricochetrobots.mojashidev.xyz/shutdown', b'asdiasjdasjddjjsaiioadsiojdosaidjasiod')

    server.join()

    print("bye...")

    
if __name__ == "__main__":
    ctrls = APIControler.APIControler()
    que = start(ctrls)
    time.sleep(1333330)
    print(que.qsize())
    stop(ctrls)