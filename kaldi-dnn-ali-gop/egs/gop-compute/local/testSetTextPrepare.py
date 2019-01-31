# with open('/home/ms2017/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/local/mispro_parse/text_mispro_new', 'r') as f:
#     content = f.readlines()
# content = [x.strip() for x in content]

# testPrefix = ['PTSNE20030128', 'PTSNE20030129', 'PTSNE20030211', 'PTSNE20030307', 'PTSNE20030403', 'PTSNE20030124', 'PTSNE20030127', 'PTSNE20030207', 'PTSNE20030305', 'PTSNE20030306']

# with open('/home/ms2017/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/local/mispro_parse/text_mispro_new_testOnly', 'w') as f:
#     for uttRow in content:
#         uttID = uttRow.split(' ')[0]
#         uttIDPrefix = uttID.split('_')[0]
#         if uttIDPrefix not in testPrefix:
#             continue
#         f.write(uttRow)
#         f.write('\n')

# with open('/home/ms2017/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/local/mispro_parse/text_mispro_new_testOnly', 'r') as f:
#     content = f.readlines()
# content = [x.strip() for x in content]

# replaceCount = 0
# with open('/home/ms2017/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/local/mispro_parse/text_mispro_new_testOnly_replaceWord', 'w') as f:
#     for row in content:
#         uttID = row.split('\t')[0] 
#         text = row.split('\t')[1].replace(' ', '')
#         textReplaceIndex = []
#         textReplaceWord = []
#         for index, syl in enumerate(text):
#             if syl == '是':
#                 replaceCount += 1
#                 textReplaceIndex.append(index)
#                 textReplaceWord.append('s4')
#         text = text.replace('是', '四')
#         f.write("{}\t{}\t{}\t{}\n".format(uttID, text, textReplaceIndex, textReplaceWord))
# print('replaceCount: ', replaceCount)

with open('/home/ms2017/kaldi/egs/pkasr/matbn_misproTestOnly/data/train/text', 'r') as f:
    content = f.readlines()
content = [x.strip() for x in content]

with open('/home/ms2017/kaldi/egs/pkasr/matbn_misproTestOnlyReplace/data/train/text', 'w') as f:
    for row in content:
        newRow = row.replace('是', ' 四')
        newRow = newRow.replace('  ', ' ')
        f.write("{}\n".format(newRow))