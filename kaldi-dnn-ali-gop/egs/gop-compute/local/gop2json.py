'''
Created on 2018/12/08
@author: Shanboy
@collaborate: Ayueh
'''
import json
import glob
import sys
import os
import math
import ast

Phones = {}
Phones_reverse = {}
Words = {}
Lexicon = {}
misDict = {}


def makeDict(phones_txt, words_txt, lexicon):

    with open(phones_txt) as f:
        for line in f:
            line = line.strip()
            phone = line.split(' ')[0]
            if phone[0] == '#':
                continue
            i = int(line.split(' ')[1])
            Phones[i] = phone
            Phones_reverse[phone] = i

    with open(words_txt) as f:
        for line in f:
            line = line.strip()
            word = line.split(' ')[0]
            i = int(line.split(' ')[1])
            Words[i] = word

    with open(lexicon) as f:
        for line in f:
            line = line.strip()
            word = line.split(' ')[0]
            phone_seq = line.split(' ')[1:]
            if word not in Lexicon:
                Lexicon[word] = []
                Lexicon[word].append(phone_seq)
            else:
                Lexicon[word].append(phone_seq)

def makeMisInfo(misInfo):
    with open(misInfo) as f:
        for line in f:
            line = line.strip()
            utt = line.split('\t')[0]
            misIndex = ast.literal_eval(line.split('\t')[2])
            misInfo = ast.literal_eval(line.split('\t')[3])

            misDict[utt] = list(zip(misIndex, misInfo))

def saveJson(Json, path):
    with open(path, 'w') as outfile:
        json.dump(Json, outfile, ensure_ascii=False)


def buildJson():
    uttInfo = {
        "version": "A.S. v.69",
        "Utterance": "",
        "text": [],
        "syl": [],
        "warningMessage": [],
        "cm": {
            "language": "Chinese",
            "score": 0,
            "timberScore": 0,
            "word": []
        }
    }

    # print('type: ', type(uttInfo))
    # print('type keys: ', uttInfo.keys())

    return uttInfo


def getGop(path):

    with open(path) as f:
        content = f.readlines()
    content = [x.strip() for x in content]

    return content


def str2list(S):
    S = S.split(' ')
    S.remove('[')
    S.remove(']')
    return S


def int2word(i):
    return Words[int(i)]


def int2phone(i):
    return Phones[int(i)]


def getPhoneIndex(phone):
    return Phones_reverse[phone]


def word2Phones(word):
    return Lexicon[Words[word]]


def getWordInfo():
    Word_info = {
        "name": "",
        "interval": [],
        "text": "",
        "timberScore": -1,
        "pitch": [],
        "volume": [],
        "timberScores": [],
        "syl": []
    }

    return Word_info

def getSylInfo():
    Syl_info = {
        "name": "",
        "text": "",
        "mispro": "",
        'sylCount': -1,
        "interval": [],
        "timberScore": -1,
        "pitch": [],
        "volume": [],
        "timberScores": [],
        "phone": []
    }
    return Syl_info


def getPhoneInfo():
    Phone_info = {
        "name": "",
        "index": 0,
        "interval": [],
        "timberScore": -1,
        "pitched": 0,
        "pitch": [],
        "volume": [],
        "cumLogLike": 0,
        "rankRatio": -1,
        "timeRatio": -1,
        "competingModelIndex": [],
        "competingModelName": [],
        "competingModelLogLike": [],
        "GOP": [],
        "timberScores": []
    }
    return Phone_info

def getPhoneGOP(phoneIndex, phoneInterval, phoneCPLogLike, phoneCPIndex):
    # print('phone index: ', phoneIndex)
    # print('phone interval: ', phoneInterval)
    # print('CPIndex: ', phoneCPIndex)

    numOfFrame = (phoneInterval[1] - phoneInterval[0]) / 0.01
    LogLike = phoneCPLogLike[phoneCPIndex.index(phoneIndex)]
    maxLogLike = phoneCPLogLike[0]
    GOP = (LogLike - maxLogLike) / numOfFrame
    # print('GOP: ', GOP)
    if GOP > 0:
        print('Bug!! GOP larger than zero!!')
    return GOP

def getPhoneScore(phoneRKR):
    a = 1 / 100
    b = 2
    Score = 100 / (1 + math.pow((phoneRKR / a), b))
    return Score

def writeUttInfo2Json(gop_score, rightSyl, uttInfo, text, utt):
    Json = buildJson()
    Json['Utterance'] = utt

    Text = ''
    Word = []
    for word in text:
        Text += int2word(word) + ' '
    Json['text'] = [Text.strip()]

    # print('rightSyl: ', rightSyl)

    Syl = '_'.join(rightSyl)
    Syl = Syl.replace("_-_", "-")
    # print('Syl: ', Syl)
    # exit()
    Json['syl'] = [Syl]

    phoneStartTime = 0.0
    # print('uttInfo: ', uttInfo)
    for i in range(len(uttInfo)):
        wordInfo = getWordInfo()
        # print('word: ', int2word(uttInfo[i]['wordName']))
        # wordInfo['name'] = Syl.split('-')[i]
        wordInfo['name'] = '_'.join(uttInfo[i]['phoneSeq'])

        ######### Shanboy 20180104 #########
        # wordInfo['text'] = int2word(uttInfo[i]['wordName'])
        wordInfo['text'] = int2word(uttInfo[i]['wordName'])

        ######### Shanboy 20180104 #########
        
        wordStartTime = phoneStartTime
        sylScore = []
        for j in range(len(uttInfo[i]['syllable'])):
            # print('j: ', j)
            sylInfo = getSylInfo()
            sylInfo['text'] = uttInfo[i]['syllable'][j]['sylText']
            sylInfo['name'] = '_'.join(uttInfo[i]['syllable'][j]['phoneSeq'])
            sylInfo['mispro'] = uttInfo[i]['syllable'][j]['mispro']
            sylInfo['sylCount'] = uttInfo[i]['syllable'][j]['sylCount']
            sylStartTime = phoneStartTime
            phoneScore = []
            for k in range(len(uttInfo[i]['syllable'][j]['phoneSeq'])):
                # print('k: ', k)
                # print('phone: ', uttInfo[i]['syllable'][j]['phoneSeq'][k])
                # print('interval: ', uttInfo[i]['syllable'][j]['interval'][k])
                phoneInfo = getPhoneInfo()

                phoneInfo['name'] = uttInfo[i]['syllable'][j]['phoneSeq'][k]

                phoneInfo['index'] = getPhoneIndex(uttInfo[i]['syllable'][j]['phoneSeq'][k])

                phoneEndTime = uttInfo[i]['syllable'][j]['interval'][k]
                phoneInfo['interval'] = [phoneStartTime, phoneEndTime]
                phoneStartTime = phoneEndTime
                
                phoneInfo['competingModelLogLike'] = uttInfo[i]['syllable'][j]['competingModelLogLike'][k]
                phoneInfo['competingModelIndex'] = uttInfo[i]['syllable'][j]['competingModelIndex'][k]
                # print('Phones: ', Phones)
                # print('yo: ', phoneInfo['competingModelIndex'])
                phoneInfo['competingModelName'] = [
                    int2phone(name) for name in uttInfo[i]['syllable'][j]['competingModelIndex'][k]]
                phoneInfo['GOP'] = getPhoneGOP(phoneInfo['index'], phoneInfo['interval'], phoneInfo['competingModelLogLike'], phoneInfo['competingModelIndex'])
                phoneInfo['rankRatio'] = phoneInfo['competingModelIndex'].index(
                    phoneInfo['index']) / len(phoneInfo['competingModelIndex'])
                # print('phoneInfo name: ', phoneInfo['name'])
                # print('phoneInfo index: ', phoneInfo['index'])
                # print('phoneInfo rankRatio: ', phoneInfo['rankRatio'])
                phoneScore_ = getPhoneScore(phoneInfo['rankRatio'])

                phoneScore.append(phoneScore_)
                phoneInfo['timberScore'] = phoneScore_

                # print('phone info: ', phoneInfo)
                sylInfo['phone'].append(phoneInfo)
            sylEndTime = phoneStartTime
            sylInfo['interval'] = [sylStartTime, sylEndTime]

            sylInfo['timberScore'] = sum(phoneScore)/float(len(phoneScore))
            sylScore.append(sylInfo['timberScore'])

            wordInfo['syl'].append(sylInfo)
        wordEndTime = phoneStartTime
        wordInfo['interval'] = [wordStartTime, wordEndTime]
        # print('word: ', wordInfo['name'])
        # print('wordInfo: ', wordInfo)
        # print('len(sylScore): ', len(sylScore))
        wordInfo['timberScore'] = sum(sylScore)/float(len(sylScore))

        Json['cm']['word'].append(wordInfo)
    # print('wordInfo: ', len(wordInfo['syl']))
    # exit()
    #     print('Json phone info: ', Json['cm']['word'][i])
    #     print('================================')
    # print('json: ', Json)
    # exit()
    return Json


def checkRightSyl(rightSyl):
    # if rightSyl[0] == 'sil':
    #     rightSyl = rightSyl[1:]
    # if rightSyl[-1] == 'sil':
    #     rightSyl = rightSyl[: -1]
    if rightSyl[-1] == '-':
        rightSyl = rightSyl[: -1]
    return rightSyl

def isFinal(phones):
    tones = ['1', '2', '3', '4', '5']
    if phones[-1] in tones:
        return True
    else:
        return False

def checkRightPhoneSeq(Phone_seq, start, phones):
    Begin = start
    rightPhoneSeq = []
    Len = 0
    # print('Phones seq: ', Phone_seq)
    # print('len of decode phone seq: ', len(phones))
    # print('Begin: ', Begin)
    for phone_seq in Phone_seq:
        decodePhones = [int2phone(phone)
                        for phone in phones[start:start + len(phone_seq)]]
        # print('phone_seq: ', [getPhoneIndex(phone) for phone in phone_seq])
        # print('decoding phones: ',
        #       phones[start:start + len(phone_seq)])
        
        if phone_seq == decodePhones:
            rightPhoneSeq = phone_seq
            Len = len(phone_seq)
            break
        else:
            continue
        # for phone in phone_seq:
        #     # print('start: ', start)
        #     # print('phone: ', phone)
        #     # print('decode phone seq: ', int2phone(phones[start]))
        #     if phone != int2phone(phones[start]):
        #         start = Begin
        #         break
        #     else:
        #         start += 1

    # Len = 0
    # rightPhoneSeq = []
    # for phone_seq in Phone_seq:
    #     Len = len(phone_seq)
    #     for i in range(len(phones)):
    #         if phones[i:i + Len] == phone_seq:
    #             rightPhoneSeq = phone_seq
    #             break

    return Len, rightPhoneSeq

def checkMisPro(sylCount, misInfo):
    for info in misInfo:
        if sylCount == info[0]:
            return info[1]
    return ""

def wordAlign(text, phones,
              interval, competing, misInfo):

    uttInfo = []
    start = 0
    sylCount = 0

    # print('decode phones: ', phones)
    # print('decode phones len: ', len(phones))

    if phones[0] == 1:
        text = [1] + text
    if phones[-1] == 1:
        text = text + [1]
    rightSyl = []
    
    # print('text: ', text)

    for word in text:
        if (word == 1) and (start != 0) and (start != len(phones) - 1)  :
            continue
            # print('Remove text sil')

        sylInfo = []
        # print('------------')
        # print('start: ', start)
        # print('word id: ', word)
        # print('word: ', Words[word])
        # print('now start phone index is: ', phones[start])
        # print('now start phone is: ', int2phone(phones[start]))
        intervals = []

        Phone_seq = word2Phones(word)
        # print('phone seq: ', Phone_seq)

        phoneSeqLen = len(Phone_seq[0])
        if len(Phone_seq) != 1:  # check wether word multipronunciations
            phoneSeqLen, rightPhoneSeq = checkRightPhoneSeq(
                Phone_seq, start, phones)
        else:
            rightPhoneSeq = Phone_seq[0]
        # rightSyl += rightPhoneSeq
        
        # print('rightPhoneSeq: ', rightPhoneSeq)
        # print('rightSyl: ', rightSyl)
        
        ######### Shanboy 20180104 #########
        S = []
        s = []
        for p in rightPhoneSeq:
            if isFinal(p):
                s.append(p)
                S.append(s)
                s = []
            else:
                s.append(p)
        if len(S) == 0:
            S = [rightPhoneSeq]
        # print('Syl: ', S)
        ######### Shanboy 20180104 #########
        
        intervals +=  interval[start:start + phoneSeqLen]
        # print('start: ', start)
        # print('intervals: ', intervals)

        ######### Shanboy 20180104 #########
        n = 0
        t = 0
        for index, sylPhone in enumerate(S):
            # print('sylPhone: ', sylPhone)
            syllableText = Words[word][index]
            # print('syllableName: ', syllableText)
            competingModelLogLike = []
            competingModelIndex = []
            
            for i in range(len(sylPhone)):
                competingIndex = list(range(1, len(Phones)))
                # print('start: ', start)
                # print('n: ', n)
                # print('phone: ', phones[start + n])
                # print('competing: ', competing[start + n])
                competingLogLike, competingIndex = (list(t) for t in zip(
                    *sorted(zip(competing[start + n], competingIndex), reverse=True)))
                competingModelLogLike.append(competingLogLike)
                competingModelIndex.append(competingIndex)
                # print('competingLogLike: ', competingLogLike)
                # print('competingIndex: ', competingIndex)
                
                n += 1
            rightSyl = rightSyl + sylPhone + ['-']
            sylInterval = intervals[ t : t + len(sylPhone) ]
            t = t + len(sylPhone)
            # print('sylInterval: ', sylInterval)

            # print('competingModelLogLike len: ', len(competingModelLogLike))
            # print('competingModelIndex len: ', competingModelIndex)
            nowCount = sylCount
            if word != 1:
                mispro = checkMisPro(sylCount, misInfo)
                sylCount += 1
            else:
                mispro = ''

            # print('mispro: ', mispro)

            sylInfoBuffer = {'sylText': syllableText,
                        'phoneSeq': sylPhone,
                        'interval': sylInterval,
                        'competingModelLogLike': competingModelLogLike,
                        'competingModelIndex': competingModelIndex,
                        'mispro': mispro,
                        'sylCount': nowCount}

            sylInfo.append(sylInfoBuffer)
            
            # print('===============')
        
        uttInfoBuffer = {'wordName': word,
                        'phoneSeq': rightPhoneSeq,
                        'interval': intervals,
                        'syllable': sylInfo
                        }

        uttInfo.append(uttInfoBuffer)
        ######### Shanboy 20180104 #########

        # for n in range(phoneSeqLen):
        #     competingIndex = list(range(1, len(Phones)))
        #     # print('start: ', start)
        #     # print('n: ', n)
        #     # print('phone: ', Phones[phones[start + n]])
        #     # print('===============')
        #     competingLogLike, competingIndex = (list(t) for t in zip(
        #         *sorted(zip(competing[start + n], competingIndex), reverse=True)))
        #     competingModelLogLike.append(competingLogLike)
        #     competingModelIndex.append(competingIndex)
            
        # uttInfoBuffer = {'wordName': word,
        #                 'phoneSeq': rightPhoneSeq,
        #                 'interval': intervals,
        #                 'competingModelLogLike': competingModelLogLike,
        #                 'competingModelIndex': competingModelIndex}

        # uttInfo.append(uttInfoBuffer)
        # print('phoneSeqLen: ', phoneSeqLen)
        start += phoneSeqLen
        # print('next start: ', start)
        # rightSyl += ['-']

        if start >= (len(phones)):
            break

        flag = True
        while flag:
            if (start <= (len(phones) - 1)) and phones[start] == 1:
                # print('sil interval: ',[interval[start]])
                # print('+++ Deal with <SIL> +++')
                silBuffer = {'wordName': '1',
                            'phoneSeq': ['sil'],
                            'interval': [interval[start]],
                            'syllable': [{'sylText': 'sil',
                                        'phoneSeq': ['sil'],
                                        'interval': [interval[start]],
                                        'competingModelLogLike': [[0]],
                                        'competingModelIndex': [[1]],
                                        'mispro': '',
                                        'sylCount': sylCount}]
                            }

                uttInfo.append(silBuffer)
                start += 1
            else:
                # print('Now phone index: ', phones[start])
                # print('Now phone: ', int2phone(phones[start]))
                flag = False
        
    # exit()
    rightSyl = checkRightSyl(rightSyl)
    # print('rightSyl: ', rightSyl)
    # print('uttInfo: ', uttInfo)
    # exit()

    return uttInfo, rightSyl

def makeJson(gop, outputDir):
    row = 0
    while row < len(gop):
        '''
        Parse GOP file
        '''
        
        utt = gop[row].split('  ')[0]
        gop_score = [float(score)
                     for score in str2list(gop[row].split('  ')[1])]
        text = [int(word) for word in str2list(gop[row + 1].split('  ')[1])]
        phones = [int(phone)
                  for phone in str2list(gop[row + 2].split('  ')[1])]

        # if utt == 'PTSND20011206_077543-080614':  # Decode error
        #     row = row + len(phones) + 4
        #     continue

        # if utt != 'PTSNE20021210_131295-132484':
        #     row = row + len(phones) + 4
        #     continue

        interval = [float(interval_)
                    for interval_ in str2list(gop[row + 3].split('  ')[1])]
        competing = []
        for i in range(row + 4, row + len(gop_score) + 4):
            competing.append([float(competing_)
                              for competing_ in str2list(gop[i].split('  ')[1])])
            # print('competing len: ', len(competing[-1]))
            # exit()
        # print('####################################')
        # print('Now utt is: ', utt)

        # print('gop_score len: ', len(gop_score))
        # uttInfo, rightSyl = wordAlign(text, phones, interval, competing)
        misInfo = misDict[utt]

        # print('misInfo: ', misInfo)

        '''
        Make uttInfo
        '''
        
        try:
            uttInfo, rightSyl = wordAlign(text, phones,
                                          interval, competing, misInfo)
        except IndexError as e:
            print('Decode error, utt is: ', utt)
            row = row + len(phones) + 4
            continue
            # exit()

        # print('==========')
        # print('Now utt: ', utt)

        '''
        Save json
        '''

        Json = writeUttInfo2Json(gop_score, rightSyl, uttInfo, text, utt)
        # print('Json: ', Json)
        
        saveJson(Json, outputDir + utt + '.json')

        global uttCount
        uttCount += 1

        row = row + len(phones) + 4
    print('Total Utterance: ', uttCount)

if __name__ == '__main__':
    uttCount = 0
    
    landDir = sys.argv[1]
    dictDir = sys.argv[2]
    gopDir = sys.argv[3]
    misInfo = sys.argv[4]

    phones_txt = landDir + '/phones.txt'
    words_txt = landDir + '/words.txt'
    lexicon = dictDir + '/lexicon.txt'
    
    makeDict(phones_txt, words_txt, lexicon)
    makeMisInfo(misInfo)

    for file in glob.glob(gopDir + '/gop.*'):
        if file.split('.')[-1] == 'txt':
            continue
        print('file: ', file)
        print('============================')
        gopInfo = getGop(file)
        if not os.path.exists(gopDir + '/parse'):
            os.makedirs(gopDir + '/parse')
        makeJson(gopInfo, gopDir + '/parse/')
    
