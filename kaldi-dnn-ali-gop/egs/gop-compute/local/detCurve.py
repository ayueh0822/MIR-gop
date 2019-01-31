import sys
import os
import shutil
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

def makeScoreVectorAndConfusionTable(uttInfo, countPhoneScoreBase, scoreConfig):
    global scoreVector, confusionTable
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
                confusionTable.append((phone['competingModelIndex'][0], phone['index']))
            sylScore = sum(phoneScore) / float(len(phoneScore))
            if len(syl['mispro']) == 0:
                scoreVector.append((sylScore, 1))
            else:
                misproCount += 1
                scoreVector.append((sylScore, 0))
    
    
def findScoreVectorThreshold(scoreVector):

    threshold = [0]
    uniqScoreVector = sorted(set(sample[0] for sample in scoreVector))
    # print('uniqScoreVector: ', uniqScoreVector)
    for i in range(len(uniqScoreVector)):
        if i == len(uniqScoreVector) -1:
            break
        threshold.append((uniqScoreVector[i] + uniqScoreVector[i+1]) / 2)
    
    threshold = threshold + [100]

    return threshold


def confusionMatrix(scoreVector, threshold):
    TP = 0
    TN = 0
    FP = 0
    FN = 0
    # print('Now utt is: ', uttInfo['Utterance'])

    for sample in scoreVector:
        if (sample[0] > threshold) and (sample[1] == 1):
            TP += 1
        elif (sample[0] > threshold) and (sample[1] == 0):
            FP += 1
        elif (sample[0] < threshold) and (sample[1] == 1):
            FN += 1
        elif (sample[0] < threshold) and (sample[1] == 0):
            TN += 1
        
    fps = FP / (FP + TN)
    fns = FN / (TP + FN)

    return fps, fns

def thresholdDecide(detFPR, detFNR, Thresholds, savePath):
    label = ['GMM', 'DNN']
    alpha = 1
    beta = 1

    for i in range(len(Thresholds)):
        axes = plt.gca()
        costByFPRFNR = [alpha * x + beta * y for x, y in zip(detFPR[i], detFNR[i])]

        plt.plot(Thresholds[i], costByFPRFNR, label=label[i])
    
        ymin = min(costByFPRFNR)
        xpos = costByFPRFNR.index(ymin)
        xmin = Thresholds[i][xpos]

        plt.annotate('cost min', xy=(xmin, ymin), xytext=(xmin, ymin)
                    )

    # Draws the key/legend
    legend = plt.legend(loc='lower left', shadow=True, fontsize='x-large')
    legend.get_frame().set_facecolor('#ffffff')

    plt.savefig(savePath)
    

def plot_legends():
    legend = plt.legend(loc='upper right',bbox_to_anchor=(1.1, 1))
    legend.get_frame().set_facecolor('#ffffff')

def show_plot():
    plt.show()

def DETCurve(detFPR, detFNR, configInfo, savePath):
    """ Plots a DET curve with the most suitable operating point based on threshold values"""
    global isTone
    plt.figure()
    for i in range(len(detFPR)):
        # Plot the DET curve based on the FAR and FRR values
        plt.plot(detFPR[i], detFNR[i], '-', label=configInfo[i])
    # Plot the optimum point on the DET Curve
    # plt.plot(far_optimum,frr_optimum, "ro", label="Suitable Operating Point")

    # Draw the default DET Curve from 1-1
    plt.plot([1.0,0.0], [0.0,1.0],"k--")

    if isTone == 'true':
        plt.title('DET Curve - with tone')
    else:
        plt.title('DET Curve - no tone')

    plt.xlabel('False positive rate')
    plt.ylabel('False negative rate')
    plt.grid(True)
    plt.axes().set_aspect('equal')

    # Draws the key/legend
    plot_legends()

    # Save plots
    plt.savefig(savePath)

    # Displays plots
    # show_plot()

def confusionTableVisualize(confusionTable, savePath):
    global isTone
    plt.figure()

    if isTone == 'true':
        numOfPhones = 176
        plt.title('Confusion Table - with tone')
    else:
        numOfPhones = 59
        plt.title('Confusion Table - no tone')

    Table = np.zeros(shape=(numOfPhones, numOfPhones))
    for phoneInfo in confusionTable:
        Table[phoneInfo[1] - 1, phoneInfo[0] - 1] += 1
    plt.imshow(Table)
    plt.colorbar()

    plt.savefig(savePath)

    return Table

def scoreVectorHistogram(scoreVector, savePath):
    global configInfo
    scoreSample = []
    for score in scoreVector:
        scoreSample.append(score[0])
    # print('scoreSample: ', scoreSample)
    plt.figure()
    plt.hist(scoreSample, bins=30)

    plt.title(configInfo[-1])
    
    plt.savefig(savePath)

def negativeHistogram(allScoreVector, savePath):
    global configInfo, isTone
    plt.figure()
    fig, axes = plt.subplots(4, 2, constrained_layout=True)
    for i, ax in enumerate(axes.flatten()):
        scoreSample = []
        for score in allScoreVector[i]:
            if score[1] == 0:
                scoreSample.append(score[0])
        ax.hist(scoreSample, bins=30)
        ax.set_title(configInfo[i])
    if isTone == 'true':
        fig.suptitle('Negative Label Histogram - with tone')
    else:
        fig.suptitle('Negative Label Histogram - no tone')
    fig.savefig(savePath)

if __name__ == "__main__":
    isTone = sys.argv[1]
    gmmDir = sys.argv[2]
    dnnDir = sys.argv[3]
    
    expDir = [gmmDir, dnnDir]
    phoneScoreBase = ['RR', 'GOP']
    phoneScoreConfig = [(0.01, 2), (0.001, 2)]
    configInfo = []
    confusionTable = []
    
    detFPR = []
    detFNR = []
    
    Thresholds = []

    tStart = time.time()

    '''
    for testing array
    '''
    allScoreVector = []

    for countPhoneScoreBase in phoneScoreBase:
        for gopDir in expDir:
            for scoreConfig in phoneScoreConfig:
                print('========================Start========================')
                gopStartTime = time.time()
                
                expModel = gopDir.split('_')[-1]
                configInfo.append("%s+%s(a=%.3f,b=%.4f)" % (expModel, countPhoneScoreBase, scoreConfig[0], scoreConfig[1]))
                print('Now preceeding the exp', configInfo[-1])

                gopParseDir = gopDir + '/parse'

                scoreVector = []

                FPR = []
                FNR = []
                thresholds = []

                fpsSum = 0
                fnsSum = 0

                '''
                Load FPR FNR pickle if exist
                '''
                pickleExist = False
                checkConfigDirPath = gopDir + '/config/' + countPhoneScoreBase + '_a-' + str(scoreConfig[0]) + '_b-' + str(scoreConfig[1])

                checkPathOne = checkConfigDirPath + '/fpr.pickle'
                checkPathTwo = checkConfigDirPath + '/fnr.pickle'
                checkPathThree = checkConfigDirPath + '/thresholds.pickle'
                checkPathFour = checkConfigDirPath + '/scoreVector.pickle'
                checkPathFive = checkConfigDirPath + '/confusionTable.pickle'
                if os.path.exists(checkPathOne) and os.path.exists(checkPathTwo) and os.path.exists(checkPathThree) and os.path.exists(checkPathFour):
                    print('Pickle Exist!!')
                    pickleExist = True
                else:
                    print('Pickle not exist, make again!')
                    os.makedirs(checkConfigDirPath, exist_ok=True)

                if pickleExist:
                    print('Pickle Loading...')
                    with open(checkPathOne, 'rb') as f:
                        FPR = pickle.load(f)
                    with open(checkPathTwo, 'rb') as f:
                        FNR = pickle.load(f)
                    with open(checkPathThree, 'rb') as f:
                        thresholds = pickle.load(f)
                    with open(checkPathFour, 'rb') as f:
                        scoreVector = pickle.load(f)
                    with open(checkPathFive, 'rb') as f:
                        confusionTable = pickle.load(f)
                    detFPR.append(FPR)
                    detFNR.append(FNR)
                    Thresholds.append(thresholds)


                '''
                Making all utt score vectors and record all phone confusion results
                '''
                if not pickleExist:
                    print('Making all utt score vectors and record all phone confusion results...')
                    scoreVectorStartTime = time.time()

                    for filename in os.listdir(gopParseDir):
                        if filename.endswith('.json'):
                            with open(gopParseDir + '/' + filename) as f:
                                uttInfo = json.load(f)
                            makeScoreVectorAndConfusionTable(uttInfo, countPhoneScoreBase, scoreConfig)
                    scoreVector.sort(key=lambda tup: tup[0])
                    scoreVectorHistogram(scoreVector, checkConfigDirPath + '/scoreHistogram.png')

                    thresholds = findScoreVectorThreshold(scoreVector)
                    print('len of threshold: ', len(thresholds))
                    Thresholds.append(thresholds)

                    scoreVectorEndTime = time.time()
                    print("scoreVector and record cost %f sec" % (scoreVectorEndTime - scoreVectorStartTime))

                    
                
                '''
                Making confusion matrix
                '''
                if not pickleExist:
                    print('Making confusion matrix...')
                    confusionMatrixStartTime = time.time()

                    for threshold in tqdm(thresholds):
                        # print('threshold: ', threshold)
                        fps, fns = confusionMatrix(scoreVector, threshold)
                        FPR.append(fps)
                        FNR.append(fns)
                    
                    detFPR.append(FPR)
                    detFNR.append(FNR)

                    confusionMatrixEndTime = time.time()
                    print("confusionMatrix cost %f sec" % (confusionMatrixEndTime - confusionMatrixStartTime))

                '''
                Save FPR & FNR & Thresholds to pickle file
                '''
                if not pickleExist:
                    with open(checkConfigDirPath + '/fpr.pickle', 'wb') as f:
                        pickle.dump(FPR, f)
                    with open(checkConfigDirPath + '/fnr.pickle', 'wb') as f:
                        pickle.dump(FNR, f)
                    with open(checkConfigDirPath + '/thresholds.pickle', 'wb') as f:
                        pickle.dump(thresholds, f)
                    with open(checkConfigDirPath + '/scoreVector.pickle', 'wb') as f:
                        pickle.dump(scoreVector, f)
                    with open(checkConfigDirPath + '/confusionTable.pickle', 'wb') as f:
                        pickle.dump(confusionTable, f)
                

                gopEndTime = time.time()
                print("gopExp cost %f sec" % (gopEndTime - gopStartTime))

                '''
                Append negative label score histogram
                '''
                allScoreVector.append(scoreVector)

                print('========================End========================')
    # negativeLabelCount = 0
    # positiveLabelCount = 0
    # for score in scoreVector:
    #     if score[1] == 0:
    #         negativeLabelCount += 1
    #     else:
    #         positiveLabelCount += 1
    # print('misproCount: ', negativeLabelCount)
    # print('rightproCount: ', positiveLabelCount)
    # print('all syl number: ', negativeLabelCount+positiveLabelCount)
    # exit()

    '''
    Check pic dir exist
    '''
    withTonePicDir = './pic/withToneTestOnlyReplace'
    noTonePicDir = './pic/noToneTestOnlyReplace'

    if isTone == 'true':
        if not os.path.exists(withTonePicDir):
            os.makedirs(withTonePicDir)
    else:
        if not os.path.exists(noTonePicDir):
            os.makedirs(noTonePicDir)

    '''
    Plot negative label score histogram
    '''
    print('Making negative label score histogram...')

    negativeLabelStartTime = time.time()
    if isTone == 'true':
        negativeHistogram(allScoreVector, withTonePicDir + '/negativeLabelHistogram.png')
    else:
        negativeHistogram(allScoreVector, noTonePicDir + '/negativeLabelHistogram.png')
    negativeLabelEndTime = time.time()

    print("negativeLabelHistogram cost %f sec" % (negativeLabelEndTime - negativeLabelStartTime))

    '''
    Plot DET Curve
    '''
    print('Making DET curve...')
    detStartTime = time.time()

    if isTone == 'true':
        DETCurve(detFPR, detFNR, configInfo, withTonePicDir + '/detCurve.png')
    else:
        DETCurve(detFPR, detFNR, configInfo, noTonePicDir + '/detCurve.png')

    detEndTime = time.time()

    print("detCurve cost %f sec" % (detEndTime - detStartTime))

    '''
    Plot confusion table
    '''
    print('Ploting confusion table...')
    confusionTableStartTime = time.time()

    if isTone == 'true':
        confusionMatrix = confusionTableVisualize(confusionTable, withTonePicDir + '/confusionTable.png')
    else:
        confusionMatrix = confusionTableVisualize(confusionTable, noTonePicDir + '/confusionTable.png')
    
    confusionTableEndTime = time.time()
    print("confusion table cost %f sec" % (confusionTableEndTime - confusionTableStartTime))
    
    '''
    Analysis confusion matrix
    '''
    phoneSet = {}

    if isTone == 'true':
        phoneSetPath = '/home/ms2017/kaldi/egs/pkasr/matbn_mispro/lang/ky92k_forpaift_v11/phones.txt'
    else:
        phoneSetPath = '/home/ms2017/kaldi/egs/pkasr/matbn_mispro/lang/no_tone_decode/phones.txt'

    with open(phoneSetPath) as f:
        for line in f:
            line = line.strip()
            phone = line.split(' ')[0]
            if phone[0] == '#':
                continue
            i = int(line.split(' ')[1])
            phoneSet[i] = phone

    confusionMatrixInfo = []
    for row in range(confusionMatrix.shape[0]):
        rowSum = sum(confusionMatrix[row, :])
        if rowSum == 0:
            continue
        rightPronounceNum = confusionMatrix[row, row]
        errorRate = 1 - ( rightPronounceNum / rowSum)
        maxErrorPatternRate = -1
        maxCol = -1
        for col in range(confusionMatrix.shape[1]):
            if row == col:
                continue
            errorPatternRate = confusionMatrix[row, col] / rowSum
            if errorPatternRate > maxErrorPatternRate:
                maxCol = col
                maxErrorPatternRate = errorPatternRate
        confusionMatrixInfo.append((phoneSet[row + 1], phoneSet[maxCol + 1], errorRate, maxErrorPatternRate))

    confusionMatrixInfo.sort(key=lambda tup: tup[2])

    if isTone == 'true':
        with open (withTonePicDir + '/phoneErrorPattern.txt', 'w') as f:
            for info in confusionMatrixInfo:
                f.write(str(info))
                f.write('\n')
    else:
        with open (noTonePicDir + '/phoneErrorPattern.txt', 'w') as f:
            for info in confusionMatrixInfo:
                f.write(str(info))
                f.write('\n')


    '''
    Plot Cost-Threshold graph
    '''
    # thresholdDecide(detFPR, detFNR, Thresholds, './pic/thresholdDecide.png')
