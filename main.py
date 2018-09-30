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

print(wapi.get_image_size(all_gid_list))

temp = {}
"""
for i in range(50):
    wapi.download_image_resize(all_gid_list[i],foldername + "\images\\" + str(i) + ".jpg",4000)

    gid = all_gid_list[i]
    data[gid] ={}
    data[gid]["aid_list"] = wapi.get_aid_of_gid(all_gid_list[i])[0]
    aid_list = data[gid]["aid_list"]
    data[gid]["numAnimals"] = len(data[gid]["aid_list"])
    data[gid]["nid_list"] = wapi.get_nid_of_aid(aid_list)
    data[gid]["species_list"] = get_species_list(aid_list)
beauty_dict = {}

"""

file_sizes = []
for i in range(50):
    info = os.stat(foldername + "\images\\" + str(i) + ".jpg")
    file_sizes.append((info.st_size)/(1024*1024.0))
    beauty_dict = beauty.extr_beauty_ftrs(foldername + "\images\\" + str(i) + ".jpg")
    #data[i]["beauty_ftrs"] = beauty.extr_beauty_ftrs(foldername + "\images\\" + str(i) + ".jpg")

print(max(file_sizes))

print(json.dumps(beauty_dict,sort_keys=True, indent=4))
print(json.dumps(data,sort_keys=True, indent=4))
