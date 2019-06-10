from PIL import Image
import math
import random
import subprocess
import sys
import time
import copy

def setwall(mp,x,y,d):
    Dir = [[0,-1],[1,0], [0,1],[-1,0]]
    mp[x][y][d] = 1
    nex = [x + Dir[d][0],y + Dir[d][1]]
    if nex[0] >= 0 and nex[1] >= 0 and nex[0] < 16 and nex[1] < 16:
        mp[nex[0]][nex[1]][(d+2)%4] = 1

        
def solve(mp, goalpos, robotpos, mainrobot):
    with subprocess.Popen("solver.exe", stdout=subprocess.PIPE,stdin = subprocess.PIPE) as p:
        instr = ""

        for i in range(16):
            for j in range(16):
                if mp[i][j][1] == 1:
                    instr += str(j) + " " + str(i) + " 1\n"
                if mp[i][j][2] == 1:
                    instr += str(j) + " " + str(i) + " 2\n"
        
        instr += "-1 -1 -1\n"

        for i in range(5):
            instr += str(robotpos[i][1]) + " " + str(robotpos[i][0]) + "\n"

        instr += str(mainrobot) + "\n"
        instr += str(goalpos[1]) + " " + str(goalpos[0]) + "\n"
        
        print(instr)

        try:
            outdata,errdata = p.communicate(input=instr.encode(), timeout=60)
        except subprocess.TimeoutExpired:
            p.kill()
            raise

        print(outdata.decode('utf-8'))

    return outdata

def rngboard():
    mp = [[[0 for k in range(4)] for i in range(16)] for j in range(16)]
    
    for i in range(16):
        setwall(mp,0,i,3)
        setwall(mp,15,i,1)
        setwall(mp,i,0,0)
        setwall(mp,i,15,2)
        
    setwall(mp,7,7,1)
    setwall(mp,7,7,2)
    setwall(mp,7,7,0)
    setwall(mp,7,7,3)
    setwall(mp,8,7,0)
    setwall(mp,8,7,1)
    setwall(mp,8,8,1)
    setwall(mp,8,8,2)
    setwall(mp,8,8,0)
    setwall(mp,8,8,3)
    setwall(mp,7,8,2)
    setwall(mp,7,8,3);


    elcount = random.randint(15,33)

    for i in range(elcount):
        x = random.randint(0, 15)
        y = random.randint(0, 15)
        d = random.randint(0, 3)
        setwall(mp,x,y,d)
        setwall(mp,x,y,(d + 1)%4)
    return mp


def ProblemGenerate(lowerbound):
    
    #while True:
    #    [y,x,d] = raw_input().split(' ')
    #    if x == '-1':
    #        break
    #    mp[int(x)][int(y)][int(d)] = 1
    #    nex = [int(x) + Dir[int(d)][0],int(y) + Dir[int(d)][1]]
    #    if nex[0] >= 0 and nex[1] >= 0 and nex[0] < 16 and nex[1] < 16:
    #        mp[nex[0]][nex[1]][(int(d)+2)%4] = 1
    
    while True:
        mp = rngboard()
        candnum = list(range(0,16*16))
        candnum.remove(7*16+7)
        candnum.remove(7*16+8)
        candnum.remove(8*16+7)
        candnum.remove(8*16+8)
        cand = [[math.floor(num/16),num%16] for num in random.sample(candnum, 6)]
        goalpos = cand[5]
        robotpos = [cand[i] for i in range(5)]
        mainrobot = random.randint(0,4)
       
        try:
            answer = solve(mp,goalpos, robotpos,mainrobot)
            if int(answer.decode('utf-8').split('\n')[0]) <= lowerbound:
                print("too short")
                continue
            break;
        except subprocess.TimeoutExpired:
            print("unsolvable")
    
    
    #pics = GenerateImage(mp,goalpos,robotpos,mainrobot)
    #pics[0].save(fname+'_base.png')
    #pics[1].save(fname+'.png')
    
    ansmoves = answer.decode('utf-8').split('\n')
    ansmoves.pop(len(ansmoves) - 1)
    optmoves = int(ansmoves[0])
    ansmoves.pop(0)
    outdict = {"problem_num":-1, "used":False,"tweet_id":-1, "board":mp, "baseimg":'',"img":'',"goalpos":goalpos,"robotpos":robotpos,"mainrobot":mainrobot,"optimal_moves":optmoves,"answer":ansmoves}
    
    return outdict


if __name__ == '__main__':
    print(ProblemGenerate(0))