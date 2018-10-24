'''
  Author: Pratik Kshirsagar
  Date  : September 29 2018
'''
try:
    import wildbook
except ImportError:
    from imageFeatures import wildbook
import os
import datetime
try:
    import beautyFtr as beauty
except ImportError:
    from imageFeatures import beautyFtr as beauty

WildbookAPI = wildbook.WildbookAPI
''' Make sure you have PyMongo installed via pip. '''
from pymongo import MongoClient as mongo

DB_URL = 'mongodb://localhost:27017/'                               ## MongoDB
SERVER_URL = 'http://pachy.cs.uic.edu:5001'                         ## IBEIS Server (pachy or other)
IMAGES_TO_ANALYZE = 100                                             ## How many images to analyze
RANDOM_GIDS = False                                                 ## Should GIDs (images) be picked randomly?
DB_NAME = 'test-new'                                                ## Name of database in MongoDB.
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
def store_image_samples(destination_dir, api, gid_list_in=None):
  gid_list=gid_list_in
  if gid_list is None:
    gid_list = api.get_all_gids()
  # print(type(gid_list))

  # print(gid_list[:10])

  ''' Shuffle the list of gid's to pick a random sample of 10 images. '''
  if RANDOM_GIDS:
      random.shuffle(gid_list)

  # print(gid_list[:IMAGES_TO_ANALYZE])

  ''' Download the images from the Wildbook API. '''
  imageList = os.listdir(destination_dir)
  image_names_list = []                                  # to see what images are already downloaded.
  for name in imageList:
    if name == '.DS_Store':                              # ignore metafiles on MacOS.
      continue                                           # convert text to int and drop off the extension.
    file_name = int(name[:-4])
    image_names_list.append(file_name)                    # create a list of images that already exist.
  # print(image_names_list)
  # print(imageList)
  number_images_to_analyze = min(IMAGES_TO_ANALYZE, len(gid_list))
  # print("Will analyze", number_images_to_analyze, " images")
  for image in range(number_images_to_analyze + 1):
    print(image)
    try:
        if gid_list[image] in image_names_list:
          print(gid_list[image], 'I EXIST')                  # skip the images that exists already on disk.
          continue
    except IndexError:
        print("List index ", image, " does not exist")
        continue
    print(gid_list[image], 'I AM BEING DOWNLOADED')
    api.download_image_resize(gid_list[image], path_join(destination_dir, str(gid_list[image]) + '.jpg'), 4000)
    print('I have downloaded: ' + str(gid_list[image]))
    # print(destination_dir + str(gid_list[i]) + '.jpg')
  return gid_list


def main(db_url=DB_URL, server_url=SERVER_URL, db_name=DB_NAME, collection_name=COLLECTION_NAME, imgs_to_analyze=IMAGES_TO_ANALYZE, rand_gids=RANDOM_GIDS, custom_gids_list=None):

  global DB_URL
  global SERVER_URL
  global DB_NAME
  global COLLECTION_NAME
  global IMAGES_TO_ANALYZE
  global RANDOM_GIDS
  DB_URL = db_url
  SERVER_URL = server_url
  DB_NAME = db_name
  COLLECTION_NAME = collection_name
  IMAGES_TO_ANALYZE = imgs_to_analyze
  RANDOM_GIDS = rand_gids

  if custom_gids_list is not None:
    IMAGES_TO_ANALYZE=len(custom_gids_list)
  client = connect_db(DB_URL)                           # connect mongodb.
  api = create_api(SERVER_URL)                          # get the api object for pachy.
  destination_dir = create_image_dir()                  # create directory to store images.
  gid_list = store_image_samples(destination_dir, api, custom_gids_list)  # store retrieved images in destination directory.
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
      'image': path_join(destination_dir, image),
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
