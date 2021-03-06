'''
  Author: Pratik Kshirsagar
  Date  : September 29 2018
'''
'''
  Edited by Lorenzo Semeria (lor.semeria@gmail.com)
  Fall 2018
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
import pymongo
import sys
import time

WildbookAPI = wildbook.WildbookAPI
''' Make sure you have PyMongo installed via pip. '''
from pymongo import MongoClient as mongo

DB_URL = 'mongodb://localhost:27017/'                               ## MongoDB
SERVER_URL =  "http://71.59.132.88:5008"    #ggr2           ## IBEIS Server (pachy or other) 'http://pachy.cs.uic.edu:5001'
IMAGES_TO_ANALYZE = 4                                          ## How many images to analyze
RANDOM_GIDS = False                                                 ## Should GIDs (images) be picked randomly?
DB_NAME = 'disposable1'                                                ## Name of database in MongoDB.
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
def create_image_dir(dir_name='images'):
  current_dir = os.getcwd()

  ''' Check if there exists an 'images' directory, else create it. '''

  if dir_name not in os.listdir(current_dir):
    os.mkdir(path_join(current_dir, dir_name))
  destination_dir = path_join(current_dir, dir_name)                ## LS - updated to be OS independent
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
  image_names_list = []                                  # to see what images are already downloaded.

  for name in os.listdir(destination_dir):
    if name == '.DS_Store':                              # ignore metafiles on MacOS.
      continue                                           # convert text to int and drop off the extension.
    try:
      file_name = int(name[:-4])
    except ValueError:
      continue
    image_names_list.append(file_name)                    # create a list of images that already exist.
  # print(image_names_list)
  number_images_to_analyze = min(IMAGES_TO_ANALYZE, len(gid_list))
  # print("Will analyze", number_images_to_analyze, " images")
  for t,gid in enumerate(gid_list[:number_images_to_analyze]):
    if t%1000 == 0:
        print("Downloading image", t, "of", number_images_to_analyze)
    sys.stdout.flush()
    if gid in image_names_list:
      #print(gid, ' appears to be here already')
      print('.', end='')
      continue
    else:
      #print('Downloading', gid, end='')
      api.download_image_resize(gid, path_join(destination_dir, str(gid) + '.jpg'), 512)
      print('|',end='')
      #print('... DONE')

    # print(destination_dir + str(gid_list[i]) + '.jpg')
  print("\nDownload finished!")
  return gid_list

def stringify_and_jpg(smth):
    ret = ''
    try:
        ret = str(smth)
        if ret.endswith('.jpg'):
            return ret
        else:
            return ret+'.jpg'
    except Exception as e:
        print("Exception in stringify", e)


def main(db_url=DB_URL, server_url=SERVER_URL, db_name=DB_NAME, collection_name=COLLECTION_NAME, imgs_to_analyze=IMAGES_TO_ANALYZE, rand_gids=RANDOM_GIDS, custom_gids_list=None, redo_beauty=False, only_boxes=False, img_dir_name='images'):

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
    custom_gids_list = list(map(int, custom_gids_list))
    IMAGES_TO_ANALYZE=len(custom_gids_list)
  client = connect_db(DB_URL)                           # connect mongodb.

  api = create_api(SERVER_URL)                          # get the api object for pachy.
  destination_dir = create_image_dir(img_dir_name)                  # create directory to store images.
  gid_list = store_image_samples(destination_dir, api, custom_gids_list)  # store retrieved images in destination directory.
  image_list = list(
                    set(
                        os.listdir(destination_dir)
                        )
                        .intersection(
                        set(
                            map(stringify_and_jpg,gid_list)
                            )
                        )
                    )            # list of all images on the directory.


  ''' Define a database.   '''
  db = client[DB_NAME]
  try:
      db[COLLECTION_NAME].create_index([('gid', pymongo.ASCENDING)], unique=True)
  except Exception:
      pass
  ''' Define a collection. '''
  images = db[COLLECTION_NAME]

  ''' Iteratively store image properties to MongoDB. '''
  if redo_beauty:
      image_list =list(os.listdir(destination_dir))
  backoff = 1
  for i, image in enumerate(image_list):
    success = False
    while not success:
        try:
            if i%200 == 0:
                print('Image', i, 'of', len(image_list), 'image is', image)
            gid = str(image).replace('.jpg','')
            aid_list = api.get_aid_of_gid(gid)[0]
            info = os.stat(path_join(destination_dir , image))
            size = info.st_size/(1024*1024.0)
            beauty_dict = beauty.extr_beauty_ftrs(path_join(destination_dir, image))
            bbox_dict = dict()
            for aid in aid_list:
                bbox_dict[aid] = api.get_bbox_of_aid(aid)
            ## BBOX = [ a, b, c, d]

            '''
            a = start X
            b = start Y
            c = increase on X axis
            d = increase on Y axis'''
            total_surface_bbox = 0
            biggest_box_area = -1
            max_aid = -1
            for aid in bbox_dict.keys():
                box = bbox_dict[aid][0]
                try:
                    a,b,c,d = box
                    total_surface_bbox = c*b
                except:
                    print(box)
                    total_surface_bbox = -1

                biggest_box_area, max_aid = max(c*b, biggest_box_area), aid if c*b>biggest_box_area else max_aid
            img_dims =  api.get_image_size(gid)[0]


            max_aid_species = -1
            box_to_image_ratio = -1
            viewpoints_list = list()
            bbox_dict = dict()

            for aid in bbox_dict.keys():
                image_area = img_dims[0]*img_dims[1]
                max_aid_species =  get_species_list([max_aid], api)
                max_aid_species = list(max_aid_species.keys())[0]
                box_to_image_ratio = total_surface_bbox / image_area
                viewpoints_list = [api.get_viewpoint_of_aid(a) for a in aid_list]
                bbox_dict = {str(k):val for (k,val) in map(lambda x: (x, bbox_dict[x]), bbox_dict.keys())}


            if only_boxes:
                add_boxes_viewpoint(gid,bbox_dict, total_surface_bbox, box_to_image_ratio, max_aid_species, viewpoints_list, images)
                success = True
                backoff = max(1, backoff/2)
            else:

                image_entry = {
                  'gid': gid,
                  'date': datetime.datetime.utcnow(),
                  'image': path_join(destination_dir, image),
                  'aid_list': aid_list,
                  'animal_count': len(aid_list),
                  'nid_list': api.get_nid_of_aid(aid_list),
                  'species_list': get_species_list(aid_list, api),
                  'dimensions': img_dims,
                  'beauty_features': beauty_dict[image],
                  'size': size,
                  'bboxes': bbox_dict,
                  'total_bboxes': total_surface_bbox,
                  'bbox_area_ratio': box_to_image_ratio,
                  'biggest_animal_species': max_aid_species,
                  'viewpoints': viewpoints_list
                }
                images.update({'gid':gid}, {'$set': image_entry}, upsert=True) # Upddate if existing or insert
                #print(image_id)
                success = True
                backoff = max(1, backoff/2)
        except Exception as e:
            print('Exception', e)
            success = False
            time.sleep(backoff)
            backoff = min(120, backoff*2)
  print('Done inserting all images')


def add_boxes_viewpoint(gid,bbox_dict, total_surface_bbox, box_to_image_ratio, max_aid_species, viewpoints_list, images):
    image_entry = {
    'bboxes': bbox_dict,
    'total_bboxes': total_surface_bbox,
    'bbox_area_ratio': box_to_image_ratio,
    'biggest_animal_species': max_aid_species,
    'viewpoints': viewpoints_list
    }
    images.update({'gid':gid}, {'$set': image_entry}, upsert=True) # Upddate if existing or insert

if __name__ == '__main__':
  main()
