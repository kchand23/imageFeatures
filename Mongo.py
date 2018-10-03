'''
  Author: Pratik Kshirsagar
  Date  : September 29 2018
'''

from wildbook import WildbookAPI
import os
import datetime
import beautyFtr as beauty

''' Make sure you have PyMongo installed via pip. '''
from pymongo import MongoClient as mongo

DB_URL = 'mongodb://localhost:27017/'                               ## MongoDB
SERVER_URL = 'http://104.42.42.134:5010'                         ## IBEIS Server (pachy or other)
IMAGES_TO_ANALYZE = 100                                             ## How many images to analyze
RANDOM_GIDS = False                                                 ## Should GIDs (images) be picked randomly?
DB_NAME = 'test1-10032018'                                                ## Name of database in MongoDB.
COLLECTION_NAME = 'images'                                          ## Name of collection in MongoDB.
path_join = os.path.join                                            ## Shorthand function

''' Connect to the MongoDB found at given URL. '''
def connect_db(url):
  client = mongo(url)
  return client

''' The random package has methods that can let us
    shuffle the sample of images.
'''
import random

''' Create a Wildbook API object. '''
def create_api(url):
  api = WildbookAPI(url)
  return api

''' Create an empty directory to store images from PACHY.
    Return the destination directory path for the images.
'''
def create_image_dir():
  current_dir = os.getcwd()

  ''' Check if there exists an 'images' directory, else create it. '''
  if 'images' not in os.listdir(current_dir):
    os.mkdir(current_dir + '/images/')
  destination_dir = path_join(current_dir, 'images')                ## LS - updated to be OS independent
  return destination_dir

''' Get list of species from a list of aids '''
def get_species_list(aid_list, api):
  speciesDict = {}
  speciesList = api.get_species_of_aid(aid_list)
  for i in speciesList:
    if i in speciesDict:
      speciesDict[i] += 1
    else:
      speciesDict[i] = 1
  return speciesDict

''' Store a random sample of images retrieved from Wildbook API '''
def store_image_samples(destination_dir, api):
  gid_list = api.get_all_gids()
  print(type(gid_list))

  print(gid_list[:10])

  ''' Shuffle the list of gid's to pick a random sample of 10 images. '''
  if RANDOM_GIDS:
      random.shuffle(gid_list)

  print(gid_list[:IMAGES_TO_ANALYZE])

  ''' Download the images from the Wildbook API. '''
  for i in range(len(gid_list)):
    api.download_image_resize(gid_list[i], path_join(destination_dir, str(gid_list[i]) + '.jpg'), 4000)
    print(destination_dir + str(gid_list[i]) + '.jpg')
  return gid_list

def main():
  client = connect_db(DB_URL)                           # connect mongodb.
  api = create_api(SERVER_URL)                          # get the api object for pachy.
  destination_dir = create_image_dir()                  # create directory to store images.
  gid_list = store_image_samples(destination_dir, api)  # store retrieved images in destination directory.
  image_list = os.listdir(destination_dir)              # list of all images on the directory.
  print(image_list)

  ''' Define a database.   '''
  db = client[DB_NAME]

  ''' Define a collection. '''
  images = db[COLLECTION_NAME]

  ''' Iteratively store image properties to MongoDB. '''
  for image in image_list:
    gid = str(image).replace('.jpg','')
    aid_list = api.get_aid_of_gid(gid)[0]
    info = os.stat(path_join(destination_dir , image))
    size = info.st_size/(1024*1024.0)
    beauty_dict = beauty.extr_beauty_ftrs(path_join(destination_dir, image))
    Image = {
      'gid': gid,
      'date': datetime.datetime.utcnow(),
      'image': (destination_dir + image),
      'aid_list': aid_list,
      'animal_count': len(aid_list),
      'nid_list': api.get_nid_of_aid(aid_list),
      'species_list': get_species_list(aid_list, api),
      'dimensions': api.get_image_size(gid)[0],
      'beauty_features': beauty_dict[image],
      'size': size
    }
    image_id = images.insert_one(Image).inserted_id
    print(image_id)


if __name__ == '__main__':
  main()
