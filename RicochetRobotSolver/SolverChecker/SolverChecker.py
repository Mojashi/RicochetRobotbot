from PIL import Image
import math
import random
import subprocess
import sys
import json
import time

def solve(mp, goalpos, robotpos, mainrobot, timeout_sec, enable_torus, enable_mirror, mirror = []):
    solver_name = "RicochetRobotSolver.exe"

    if enable_mirror or enable_torus:
        solver_name = "solver_g.exe"

    with subprocess.Popen(solver_name, stdout=subprocess.PIPE,stdin = subprocess.PIPE) as p:
        instr = ""

        for i in range(16):
            for j in range(16):
                if mp[i][j][0] == 1:
                    instr += str(j) + " " + str(i) + " 0\n"
                if mp[i][j][1] == 1:
                    instr += str(j) + " " + str(i) + " 1\n"
                if mp[i][j][2] == 1:
                    instr += str(j) + " " + str(i) + " 2\n"
                if mp[i][j][3] == 1:
                    instr += str(j) + " " + str(i) + " 3\n"
        
        instr += "-1 -1 -1\n"
        
        for mr in mirror:
           instr += str(mr[1]) + ' ' + str(mr[0]) + ' ' + str(mr[2]) + ' ' + str(mr[3]) +'\n'

        instr += '-1 -1 -1 -1\n'

        for i in range(5):
            instr += str(robotpos[i][1]) + " " + str(robotpos[i][0]) + "\n"

        instr += str(mainrobot) + "\n"
        instr += str(goalpos[1]) + " " + str(goalpos[0]) + "\n"
        
        print(instr)

        try:
            outdata,errdata = p.communicate(input=instr.encode(), timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            p.kill()
            raise

        print(outdata.decode('utf-8'))

    return outdata



with open("history.json") as hf:
    problems = json.load(hf)

for p in problems.keys():
    with open("problems/" + str(p) + ".json") as f:
        dict = json.load(f)
        board = dict["board"]
        goalpos = dict["goalpos"]
        robotpos = dict["robotpos"]
        mainrobot = dict["mainrobot"]
        answer = dict["answer"]
        print(str(p))
        try:
           out = solve(board, goalpos, robotpos, mainrobot, 30, True, True, [])
        except subprocess.TimeoutExpired:
            print("TLE")
            continue

        newanswer = out.decode('utf-8').split('\n')

        if int(answer[0]) < int(newanswer[0]):
            print("new is broken num " + str(p))

        if int(answer[0]) > int(newanswer[0]):
            print("old is broken num " + str(p))