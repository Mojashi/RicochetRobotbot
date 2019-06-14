import time
import multiprocessing
from flask import Flask, request
import base64
import hashlib
import hmac
import json
import urllib.parse
from requests_oauthlib import OAuth1Session
import requests
import APIControler

app = Flask(__name__)

env_name = "mojashdev"
my_ip = None
webhook_id = None

que = multiprocessing.Queue()
ctrl = None

def get_myip():
    res = requests.get("http://inet-ip.info/ip")
    my_ip = res.text

@app.url_value_preprocessor
def add_user_info(endpoint, values):
    global que
    if not endpoint is None:
        values["que"] = que

# Defines a route for the GET request
@app.route('/webhooks/twitter', methods=['GET'])
def webhook_challenge():
    global ctrl

    # creates HMAC SHA-256 hash from incomming token and your consumer secret
    sha256_hash_digest = hmac.new(ctrl.CONSUMER_SECRET, msg=request.args.get('crc_token'), digestmod=hashlib.sha256).digest()
    
    # construct response data with base64 encoded hash
    response = {
      'response_token': 'sha256=' + base64.b64encode(sha256_hash_digest)
    }
    
    # returns properly formatted json response
    return json.dumps(response)

@app.route('/webhooks/twitter',methods=['POST'])
def index(que):
    if request.headers['Content-Type'] != 'application/json':
        if "direct_message_events" in json.loads(request.json).key():
            que.put(request.json)
        print(request.json)
    return "OK"

def run(que_al, ctrl_al):
    global ctrl
    global que
    ctrl = ctrl_al
    que = que_al
    api.run(host='0.0.0.0', port=443, ssl_context=('openssl/server.crt', 'openssl/server.key'), threaded=False, debug=True)

    #app.run(debug=False, host="0.0.0.0", port = 80)

server = None
running = False


def getmsgs():
    global que
    msgs = []


    while que.not_empty():
        msgs.extend(que.get()["direct_message_events"])
    
    return msgs

def subscribe(ctrls):
    global webhook_id

    my_url = my_ip + "443"
    sub_url = "https://api.twitter.com/1.1/account_activity/all/" + env_name + "/webhooks.json?url=" +urllib.parse.quote(my_url)

    
    req = ctrls.twitter.post(url=sub_url)

    if req.status_code == 200:
        print ("subscribed")
    else:
        print("subscribe failed")

    webhook_id = req.json()["id"]
    
    sub_url  ="https://api.twitter.com/1.1/account_activity/all/" + env_name + "/subscriptions.json"
    req = ctrls.twitter.post(url = sub_url)

    return 

def unsubscribe(ctrls):
    global webhook_id

    unsub_url = "https://api.twitter.com/1.1/account_activity/all/"+env_name+"/subscriptions.json"

    ctrls.twitter.delete(url = unsub_url)

    unsub_url = "https://api.twitter.com/1.1/account_activity/all/"+env_name+"/webhooks/"+ str(webhook_id) + ".json"
    
    ctrls.twitter.delete(url = unsub_url)

    return

def start(ctrl):
    global running
    global server
    global que

    if running == True:
        return que

    running = False


    print("starting process")
    server = multiprocessing.Process(target=run, args=(que,ctrl,))
    server.start()

    time.sleep(1)
    
    subscribe(ctrls)

    return que


def stop():
    global running
    global server

    if running == False:
        return

    running = False

    unsubscribe(ctrls)

    server.terminate()
    server.join()

    print("bye...")

    
if __name__ == "__main__":
    ctrls = APIControler.APIControler()
    que = start(ctrls)
    time.sleep(100)
    print(que.qsize())
    stop()