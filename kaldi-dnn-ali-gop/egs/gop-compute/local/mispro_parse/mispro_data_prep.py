import re
import os
from pathlib import Path
import jieba

def particle2syl(particle_dict):
    par2syl = {}
    with open (particle_dict, "r") as f:
        content = f.readlines()
    content = [x.strip() for x in content] 

    for line in content:
        partcle = line.split(" ")[0]
        syl = line.split(": ")[-1][:-1]
        if syl == '<UK>':
            syl = 'U'
        par2syl[partcle] = syl
    # print(par2syl)
    return par2syl

def parser(std_data_dir):
    data_dict = {}
    totalMisUtts = 0
    totalMisPhones = 0
    for data_part in ["train", "dev", "test"]:

        std_segments = "{}/data_par/{}/text".format(std_data_dir, data_part)
        std_seg_dict = {}
        with open(std_segments, "r") as f:
            for line in f:
                std_seg_id = line.split(" ", 1)[0]
                std_seg_text = line.split(" ", 1)[1].strip()
                std_seg_dict[std_seg_id] = std_seg_text

        # print (std_seg_dict)
        # exit()

        trs_dir = "{}/trs/{}/".format(std_data_dir, data_part)
        trs_list = []
        for root, dirs, files in os.walk(trs_dir):
            files.sort()
            for f in files:
                if f == ".DS_Store":
                    continue
                if "name" not in f:
                    trs_list.append(root + f)
                    utt = f.split(".")[0]
                    data_dict[utt] = {"wav": "{}/{}.wav".format(data_part, utt),
                                      "seg": []}

        # print (data_dict)
        # exit()
        total = 0
        total_mis = 0
        for trs_path in trs_list:
            with open(trs_path, "r", encoding="utf-8") as f:
                xml_content = f.read()
            utt = trs_path.split("/")[8].split(".")[0]

            # =========================== PARSE ==========================
            cnt = 0
            mis_count = 0
            turn_pattern = r"<Turn speaker=\"(?P<spkr_name>.*?)\".*?startTime=\"(?P<start_time>.*?)\" endTime=\"(?P<end_time>.*?)\">(?P<turn_content>.*?)</Turn>"
            turn = re.compile(turn_pattern, re.DOTALL)
            # print(trs_path)

            for i, trun_match in enumerate(turn.finditer(xml_content)):
                # print (trun_match.group("spkr_name"), trun_match.group("start_time"), trun_match.group("end_time"))
                
                turn_content = trun_match.group("turn_content")
                sync_pattern = r"<Sync time=\"(?P<start_time>.*?)\"/>(?P<sync_content>.*?)<Sync time=\"(?P<end_time>.*?)\"/>"
                sync = re.compile(sync_pattern, re.DOTALL)

                for sync_match in sync.finditer(turn_content):
                    syl_index = 0
                    sync_content = sync_match.group("sync_content")
                    ch_word = re.compile(u"[\u4e00-\u9fa5]+")
                    # ch_text = .search(sync_content)
                    mis_pattern = r"<Event desc=\"mispronunciation (?P<mis_pro>.*?)\" type=\"pronounce\" extent=\"previous\"/>"
                    mis = re.compile(mis_pattern, re.DOTALL)

                    particle_pattern = r"<Event desc=\"particle\" type=\"noise\" extent=\"begin\"/>"
                    particle = re.compile(particle_pattern, re.DOTALL)

                    seg_tmp = {"seg_id": "",
                               "start": 0.0,
                               "end": 0.0,
                               "content": "",
                               "mispro_index":[],
                               "mispro_info":[]
                               }

                    if mis.search(sync_content):
                        # print ("{} strat={} end={}".format( trun_match.group("spkr_name"), trun_match.group("start_time"), trun_match.group("end_time") ))
                        seg_tmp["start"] = float(
                            sync_match.group("start_time")[:-1])
                        seg_tmp["end"] = float(sync_match.group(
                            "end_time").split("\"")[0][:-1])
                        seg_id = "{}_{:07.2f}-{:07.2f}".format(
                            utt, seg_tmp["start"], seg_tmp["end"]).replace(".", "")
                        # print (seg_id)
                        # exit()
                        particle_flag = False
                        
                        for line in sync_content.split("\n"):
                            if line.split(' ')[0][1:] == 'Comment':
                                continue
                            if  "<Event desc=\"particle\" type=\"noise\" extent=\"begin\"/>" == line:
                                particle_flag = True
                                continue
                            if  "<Event desc=\"particle\" type=\"noise\" extent=\"end\"/>" == line:
                                particle_flag = False
                                continue

                            if mis.search(line):
                                for mis_match in mis.finditer(line):
                                    mis_count += 1
                                    seg_tmp["mispro_index"] += [syl_index]
                                    seg_tmp["mispro_info"] += [mis_match.group("mis_pro")]
                                    

                            else:
                                for ch_text in ch_word.finditer(line):
                                    # print('text group: ', ch_text.group())
                                    seg_tmp["content"] += ch_text.group()

                                if particle_flag:
                                    if utt == 'PTSNE20030129' and par2syl.setdefault(line, 'U') == 'U':
                                    seg_tmp["content"] += par2syl.setdefault(line, 'U')
                                    # print (ch_text.group(),end=' ')
                            syl_index = len(seg_tmp["content"]) - 1

                        if seg_id in std_seg_dict:
                            seg_tmp["seg_id"] = seg_id
                            seg_tmp["content"] = std_seg_dict[seg_id]
                            cnt += 1
                            data_dict[utt]["seg"].append(seg_tmp)
                        
                        # print(seg_tmp)
                        # exit()

            total += cnt
            total_mis += mis_count
            # print("============= mis utt", cnt)
        totalMisUtts += total
        totalMisPhones += total_mis
        print("total number of mispronounce in " + data_part + ": " + str(total) + " utts, " + str(total_mis) + " syllables.")
    print('====================================================')
    print('Total number of mispronounce in dataset : ' + str(totalMisUtts) + ' utts, ' + str(totalMisPhones) + " syllables.")
    return data_dict


def make_wavscp(data_dict):
    with open("wav.scp", "w") as f:
        for utt in data_dict:
            f.write("{} {}\n".format(utt, data_dict[utt]["wav"]))


def make_segment(data_dict):
    with open("segments", "w") as f:
        for utt in data_dict:
            for segg in data_dict[utt]["seg"]:
                t1 = segg["start"]
                t2 = segg["end"]
                # seg_id = "{}_{:07.2f}-{:07.2f}".format(utt, t1, t2).replace(".","")
                f.write("{} {} {} {}\n".format(
                    segg["seg_id"], utt, str(t1), str(t2)))


def make_utt2spk(data_dict):
    with open("utt2spk", "w") as f:
        for utt in data_dict:
            for segg in data_dict[utt]["seg"]:
                # t1 = segg["start"]
                # t2 = segg["end"]
                # seg_id = "{}_{:07.2f}-{:07.2f}".format(utt, t1, t2).replace(".","")
                f.write("{} {}\n".format(segg["seg_id"], segg["seg_id"]))


def make_text(data_dict):
    # jieba.initialize()
    # jieba.set_dictionary("ky92k_forpaift_v11/word_list.txt")
    with open("text", "w") as f:
        for utt in data_dict:
            for segg in data_dict[utt]["seg"]:
                # t1 = segg["start"]
                # t2 = segg["end"]

                # seg_id = "{}_{:07.2f}-{:07.2f}".format(utt, t1, t2).replace(".","")

                # cache = Path("/tmp/jieba.cache")
                # if cache.exists():
                #     os.remove(str(cache))

                # content = jieba.cut(segg["content"], HMM=False)
                # print(' '.join(content))
                # exit()
                f.write("{} {}\n".format(segg["seg_id"], segg["content"]))
                # f.write("{} {}\n".format(seg_id, segg["content"]))


def make_misInfoText(data_dict):
    with open("text_mispro_new", "w") as f:
        for utt in data_dict:
            for segg in data_dict[utt]["seg"]:
                # lst = map(str, segg["mispro_info"])            
                # mispro_info = ", ".join(lst)
                f.write("{}\t{}\t{}\t{}\n".format(segg["seg_id"], segg["content"], segg["mispro_index"], segg["mispro_info"]))


if __name__ == "__main__":

    std_data_dir = "/mnt/hdd18.2t/dataset/IISASR/MATBN-200"
    particle_dict = "./particle_supplement_list.txt"

    par2syl = particle2syl(particle_dict)
    data_dict = parser(std_data_dir)

    # make_wavscp(data_dict)
    # make_segment(data_dict)
    # make_utt2spk(data_dict)
    # make_text(data_dict)

    make_misInfoText(data_dict)
