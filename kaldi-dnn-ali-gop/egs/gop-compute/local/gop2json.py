'''
Created on 2018/12/08
@author: Shanboy
@collaborate: Ayueh
'''
import json
import glob
import sys
import os

Phones = {}
Phones_reverse = {}
Words = {}
Lexicon = {}


def makeDict(phones_txt, words_txt, lexicon):

    with open(phones_txt) as f:
        for line in f:
            line = line.strip()
            phone = line.split(' ')[0]
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


def saveJson(Json, path):
    with open(path, 'w') as outfile:
        json.dump(Json, outfile, ensure_ascii=False)


def buildJson():
    uttInfo = {
        "version": "A.S. v.69",
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
        "phone": []
    }
    return Word_info


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
        "timberScores": []
    }
    return Phone_info


def writeUttInfo2Json(gop_score, rightSyl, uttInfo, text):
    Json = buildJson()
    Text = ''
    Word = []
    for word in text:
        Text += int2word(word) + ' '
    Json['text'] = [Text.strip()]

    Syl = '_'.join(rightSyl)
    Syl = Syl.replace("_-_", "-")
    Json['syl'] = [Syl]

    phoneStartTime = 0.0
    for i in range(len(uttInfo)):
        # print('word: ', uttInfo[i]['wordName'])
        wordInfo = getWordInfo()
        wordInfo['name'] = Syl.split('-')[i]
        wordInfo['text'] = int2word(uttInfo[i]['wordName'])
        wordStartTime = phoneStartTime

        for j in range(len(uttInfo[i]['phoneSeq'])):
            # print('phone: ', uttInfo[i]['phoneSeq'][j])
            # print('interval: ', uttInfo[i]['interval'][j])
            phoneInfo = getPhoneInfo()

            phoneInfo['name'] = uttInfo[i]['phoneSeq'][j]

            phoneInfo['index'] = getPhoneIndex(uttInfo[i]['phoneSeq'][j])

            phoneEndTime = uttInfo[i]['interval'][j]
            phoneInfo['interval'] = [phoneStartTime, phoneEndTime]
            phoneStartTime = phoneEndTime

            phoneInfo['competingModelLogLike'] = uttInfo[i]['competingModelLogLike'][j]
            phoneInfo['competingModelIndex'] = uttInfo[i]['competingModelIndex'][j]
            phoneInfo['competingModelName'] = [
                int2phone(name) for name in uttInfo[i]['competingModelIndex'][j]]

            phoneInfo['rankRatio'] = phoneInfo['competingModelIndex'].index(
                phoneInfo['index']) / len(phoneInfo['competingModelIndex'])

            # print('phone info: ', phoneInfo)
            wordInfo['phone'].append(phoneInfo)

        wordEndTime = phoneStartTime
        wordInfo['interval'] = [wordStartTime, wordEndTime]
        Json['cm']['word'].append(wordInfo)
    #     print('Json phone info: ', Json['cm']['word'][i])
    #     print('================================')
    # print('json: ', Json)

    return Json


def checkRightSyl(rightSyl):
    # if rightSyl[0] == 'sil':
    #     rightSyl = rightSyl[1:]
    # if rightSyl[-1] == 'sil':
    #     rightSyl = rightSyl[: -1]
    if rightSyl[-1] == '-':
        rightSyl = rightSyl[: -1]
    return rightSyl


def checkRightPhoneSeq(Phone_seq, start, phones):
    Begin = start
    rightPhoneSeq = []
    Len = 0
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


def wordAlign(text, phones,
              interval, competing):

    uttInfo = []
    start = 0

    # print('decode phones: ', phones)
    # print('decode phones len: ', len(phones))
    if phones[0] == 1:
        text = [1] + text
    if phones[-1] == 1:
        text = text + [1]
    rightSyl = []

    for word in text:
        # print('------------')
        # print('word: ', Words[word])
        intervals = []
        competingModelLogLike = []
        competingModelIndex = []
        # competingIndex = list(range(1, 176))

        Phone_seq = word2Phones(word)
        # print('phone seq: ', Phone_seq)

        phoneSeqLen = len(Phone_seq[0])
        if len(Phone_seq) != 1:  # check wether word multipronunciations
            phoneSeqLen, rightPhoneSeq = checkRightPhoneSeq(
                Phone_seq, start, phones)
        else:
            rightPhoneSeq = Phone_seq[0]
        rightSyl += rightPhoneSeq

        intervals += interval[start:start + phoneSeqLen]
        for n in range(phoneSeqLen):
            competingIndex = list(range(1, 176))
            # print('start: ', start)
            # print('n: ', n)
            # print('phone: ', Phones[phones[start + n]])
            # print('===============')
            competingLogLike, competingIndex = (list(t) for t in zip(
                *sorted(zip(competing[start + n], competingIndex), reverse=True)))
            competingModelLogLike.append(competingLogLike)
            competingModelIndex.append(competingIndex)

        start += phoneSeqLen

        uttInfoBuffer = {'wordName': word,
                         'phoneSeq': rightPhoneSeq,
                         'interval': intervals,
                         'competingModelLogLike': competingModelLogLike,
                         'competingModelIndex': competingModelIndex}

        uttInfo.append(uttInfoBuffer)
        rightSyl += ['-']

        if start >= len(phones):
            break

        if phones[start] == 1 and start != len(phones) - 1:
            start += 1

    rightSyl = checkRightSyl(rightSyl)

    return uttInfo, rightSyl


def makeJson(gop, outputDir):
    row = 0
    while row < len(gop):
        utt = gop[row].split('  ')[0]
        gop_score = [float(score)
                     for score in str2list(gop[row].split('  ')[1])]
        text = [int(word) for word in str2list(gop[row + 1].split('  ')[1])]
        phones = [int(phone)
                  for phone in str2list(gop[row + 2].split('  ')[1])]

        # if utt == 'PTSND20011206_077543-080614':  # Decode error
        #     row = row + len(phones) + 4
        #     continue

        # if utt != 'PTSND20011107_064844-065017':
        #     row = row + len(phones) + 4
        #     continue

        interval = [float(interval_)
                    for interval_ in str2list(gop[row + 3].split('  ')[1])]
        competing = []
        for i in range(row + 4, row + len(gop_score) + 4):
            competing.append([float(competing_)
                              for competing_ in str2list(gop[i].split('  ')[1])])
        # print('####################################')
        # print('Now utt is: ', utt)

        # print('gop_score len: ', len(gop_score))
        try:
            uttInfo, rightSyl = wordAlign(text, phones,
                                          interval, competing)
        except IndexError:
            print('Decode error, utt is: ', utt)
            row = row + len(phones) + 4
            continue
            # print('rightSyl: ', rightSyl)
            # exit()
            # print('uttInfo: ', uttInfo[0])
            # exit()

        Json = writeUttInfo2Json(gop_score, rightSyl, uttInfo, text)
        # print('Json: ', Json)
        # saveJson(Json, 'PTSND20011107_064844-065017.json')
        saveJson(Json, outputDir + utt + '.json')
        # exit()
        row = row + len(phones) + 4


if __name__ == '__main__':

    landDir = sys.argv[1]
    dictDir = sys.argv[2]
    gopDir = sys.argv[3]

    phones_txt = landDir + '/phones.txt'
    words_txt = landDir + '/words.txt'
    lexicon = dictDir + '/lexicon.txt'

    makeDict(phones_txt, words_txt, lexicon)
    # gopInfo = getGop('./gop.t')
    # makeJson(gopInfo, gopDir + '/parse/')

    for file in glob.glob(gopDir + '/gop.*'):
        if file.split('.')[-1] == 'txt':
            continue
        print('file: ', file)
        print('============================')
        gopInfo = getGop(file)
        if not os.path.exists(gopDir + '/parse'):
            os.makedirs(gopDir + '/parse')
        makeJson(gopInfo, gopDir + '/parse/')
