import pyrebase
import json

class Service:
  __instance = None

  __app = None
  __storage = None
  __config = None

  def __new__(cls, *args, **kwargs):
    if cls.__instance is None:
      cls.__instance = super().__new__(cls)
 
    return cls.__instance
  
  def __init__(self, path_storage_config="firebase_storage.json", local_path="./photos/", firebase_path="gallery/"):
    self.__LOCAL_PATH = local_path
    self.__REMOTE_PATH = firebase_path

    self.__load_storage(path_storage_config)
    self.__app = pyrebase.initialize_app(self.__config)
    self.__storage = self.__app.storage()

  def __load_storage(self, path='firebase_storage.json'):
    self.__config = json.load(open(path, 'rb'))

  # POST
  def post_photo(self, from_local_path: str, to_url: str):

    url = to_url.split("/")[1]
    print()
    print(self.__REMOTE_PATH + url)
    print(from_local_path)
    print()
    try:
      self.__storage.child(self.__REMOTE_PATH + url).put(from_local_path)
    except Exception as e:
      print("ERROR: POST PHOTO")
      return None
    
    return "200"

  # GET
  def get_photo(self, to_local_path: str, from_url: str):

    print()
    print(self.__REMOTE_PATH + from_url)
    print(to_local_path)
    print()
  
    try:
      self.__storage.child(self.__REMOTE_PATH + from_url).download(path=self.__LOCAL_PATH, filename=to_local_path)
    except Exception as e:
      print("ERROR: GET PHOTO")
      return None

    return "200"
  
