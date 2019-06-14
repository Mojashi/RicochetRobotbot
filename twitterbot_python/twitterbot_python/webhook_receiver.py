import time
import multiprocessing
from flask import Flask, request
import json

app = Flask(__name__)
que = multiprocessing.Queue()
@app.url_value_preprocessor
def add_user_info(endpoint, values):
    global que
    if not endpoint is None:
        values["que"] = que

@app.route('/',methods=['POST'])
def index(que):
    que.put(request.data)
    print(request.data)
    print(que.qsize())
    return "OK"

def run(que_al):
    global que
    que = que_al
    app.run()

server = None
running = False

def start():
    global running
    global server
    global que

    if running == True:
        return que

    running = False


    print("starting process")
    server = multiprocessing.Process(target=run, args=(que,))
    server.start()
    return que


def stop():
    global running
    global server

    if running == False:
        return

    running = False

    server.terminate()
    server.join()

    print("bye...")

    
if __name__ == "__main__":
    que = start()
    time.sleep(10)
    print(que.qsize())
    stop()