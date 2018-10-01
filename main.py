from wildbook import WildbookAPI
import os
import json
import beautyFtr as beauty
import random

def get_species_list(aid_list):
    speciesDict = {}
    speciesList = wapi.get_species_of_aid(aid_list)
    for i in speciesList:
        if i in speciesDict:
            speciesDict[i] += 1
        else:
            speciesDict[i] = 1
    return speciesDict

data = {}

dirpath = os.getcwd()
foldername = os.getcwd()

wapi = WildbookAPI('http://pachy.cs.uic.edu:5001')
all_gid_list = wapi.get_all_gids()

temp = {}
for i in range(5):
    gid = int(all_gid_list[i])
    wapi.download_image_resize(all_gid_list[i],foldername + "\images\\" + str(gid) + ".jpg",4000)
    data[gid] ={}
    data[gid]["aid_list"] = wapi.get_aid_of_gid(all_gid_list[i])[0]
    aid_list = data[gid]["aid_list"]
    data[gid]["numAnimals"] = len(data[gid]["aid_list"])
    data[gid]["nid_list"] = wapi.get_nid_of_aid(aid_list)
    data[gid]["species_list"] = get_species_list(aid_list)
    data[gid]["dimensions"] = wapi.get_image_size(gid)[0]
beauty_dict = {}


file_sizes = []
for i in range(5):
    gid = int(all_gid_list[i])
    info = os.stat(foldername + "\images\\" + str(gid) + ".jpg")
    size = (info.st_size)/(1024*1024.0)
    file_sizes.append(size)
    beauty_dict = beauty.extr_beauty_ftrs(foldername + "\images\\" + str(gid) + ".jpg")
    data[gid].update(beauty_dict[str(gid)+".jpg"])
    data[gid]["size_in_MB"] = size

print(max(file_sizes))

print(json.dumps(data,sort_keys=True, indent=4))

