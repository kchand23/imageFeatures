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
from bson.binary import Binary

## LS - added to more easily change server
DB_URL = 'mongodb://localhost:27017/'
SERVER_URL = 'http://pachy.cs.uic.edu:5001'

path_join = os.path.join
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
  destination_dir = os.path.join(current_dir, 'images') ## LS - updated to be OS independent
  return destination_dir

def get_species_list(aid_list, api):                     # ?!
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
  random.shuffle(gid_list)

  print(gid_list[:4])

  ''' Download the images from the Wildbook API. '''
  for i in range(4):
    api.download_image_resize(gid_list[i], os.path.join(destination_dir, str(gid_list[i]) + '.jpg'), 4000)
    print(destination_dir + str(gid_list[i]) + '.jpg')
  return gid_list

def main():
  client = connect_db(DB_URL)     # connect mongodb.
  api = create_api(SERVER_URL)      # get the api object for pachy.
  destination_dir = create_image_dir()                  # create directory to store images.
  gid_list = store_image_samples(destination_dir, api)  # store retrieved images in destination directory.
  image_list = os.listdir(destination_dir)              # list of all images on the directory.
  print(image_list)

  ''' Define a database.   '''
  db = client['image-db']

  ''' Define a collection. '''
  images = db['images']

  ''' Iteratively store image properties to MongoDB. '''
  for image, gid in zip(image_list, gid_list):
    aid_list = api.get_aid_of_gid(gid)[0]
    info = os.stat(os.path.join(destination_dir , image))
    size = info.st_size/(1024*1024.0)
    beauty_dict = beauty.extr_beauty_ftrs(destination_dir + image)
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
