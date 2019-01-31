import re
import os

for trs_part in ["train", "dev", "test"]:
    print ("==========================================")
    print ("                 {}                       ".format(trs_part))
    print ("==========================================")
    trs_dir = "./trs/" + trs_part + "/"
    trs_list = []
    for root, dirs, files in os.walk(trs_dir) :
        files.sort()
        for f in files:
            if f == ".DS_Store":
                continue
            if "name" not in f:
                trs_list.append(root + f)
# trs_path = "./trs/train/PTSND20011107.trs"
# with open(trs_path, "r", encoding="big5") as f:
#     xml_content = f.read()

# gg = re.search("mispronunciation", xml_content)
# gg = re.findall("mispronunciation",xml_content)
    total = 0
    for trs_path in trs_list:
        with open(trs_path, "r", encoding="big5") as f:
            xml_content = f.read()
        cnt = 0
        turn_pattern = r"<Turn speaker=\"(?P<spkr_name>.*?)\".*?startTime=\"(?P<start_time>.*?)\" endTime=\"(?P<end_time>.*?)\">(?P<turn_content>.*?)</Turn>"
        turn = re.compile(turn_pattern, re.DOTALL)
        print (trs_path)
        for i, trun_match in enumerate(turn.finditer(xml_content)):
            # print (trun_match.group("spkr_name"), trun_match.group("start_time"), trun_match.group("end_time"))
            turn_content = trun_match.group("turn_content")
            sync_pattern = r"<Sync time=\"(?P<start_time>.*?)\"/>(?P<sync_content>.*?)<Sync time=\"(?P<end_time>.*?)\"/>"
            sync = re.compile(sync_pattern, re.DOTALL)
            for sync_match in sync.finditer(turn_content):
                sync_content = sync_match.group("sync_content")
                cht_word = re.compile(u"[\u4e00-\u9fa5]+")
                # cht_text = cht_word.search(sync_content)
                mis_pattern = r"<Event desc=\"mispronunciation (?P<mis_pro>.*?)\" type=\"pronounce\" extent=\"previous\"/>"
                mis = re.compile(mis_pattern, re.DOTALL)

                if mis.search(sync_content):
                    print ("{} strat={} end={}".format( trun_match.group("spkr_name"), trun_match.group("start_time"), trun_match.group("end_time") ))
                    cnt += 1
                    for line in sync_content.split("\n"):
                        if mis.search(line):
                            for mis_match in mis.finditer(line):
                                print ("[{}]".format(mis_match.group("mis_pro")),end=' ')
                        else :
                            for cht_text in cht_word.finditer(line):
                                print (cht_text.group(),end=' ')
                    print()
        total += cnt
        print("============= mis utt", cnt)
    print ("total", total)