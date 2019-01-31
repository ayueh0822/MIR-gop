import sys
import os
import json
import numpy as np
import pickle
from decimal import Decimal
import time
import math
from tqdm import tqdm

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

def getPhoneRRScore(phoneRKR, scoreConfig):
    a = scoreConfig[0]
    b = scoreConfig[1]
    Score = 100 / (1 + math.pow((phoneRKR / a), b))
    return Score

def getPhoneGOPScore(phoneGOP, scoreConfig):
    a = scoreConfig[0]
    b = scoreConfig[1]
    Score = 100 / (1 + math.pow((-phoneGOP / a), b))
    return Score

uttID = 'PTSNE20030211_067311-067949'
filename = '/home/ms2017/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/matbn_mispro_noTone_testOnly_tri5_gmm/parse/' + uttID + '.json'

countPhoneScoreBase = 'GOP'
scoreConfig = (0.01, 2)

allSylScore = []

with open(filename) as f:
    uttInfo = json.load(f)
    for word in uttInfo['cm']['word']:
        if word['name'] == 'sil':
            continue
        for syl in word['syl']:
            phoneScore = []
            for phone in syl['phone']:
                if countPhoneScoreBase == 'RR':
                    phoneScore.append(getPhoneRRScore(phone['rankRatio'], scoreConfig))
                if countPhoneScoreBase == 'GOP':
                    phoneScore.append(getPhoneGOPScore(phone['GOP'], scoreConfig))
            sylScore = sum(phoneScore) / float(len(phoneScore))
            if len(syl['mispro']) != 0:
                allSylScore.append((syl['text'], sylScore, 0))
            else:
                allSylScore.append((syl['text'], sylScore, 1))
print(allSylScore)

plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False

plt.figure()
plt.title('Sentence Example - no tone, GMM+GOP')

barList = plt.bar([x[0] for x in allSylScore], [x[1] for x in allSylScore])

for index, syl in enumerate(allSylScore):
    if syl[2] == 0:
        barList[index].set_color('r')

plt.savefig('./pic/noToneTestOnly/sentenceBar.png')

