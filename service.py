import pyrebase

config = {
  "apiKey": "AIzaSyB39yl0BjlMeI44iP91mBGGCqL4BcrMelk",
  "authDomain": "tg-recsys-bot.firebaseapp.com",
  "databaseURL": "https://tg-recsys-bot-default-rtdb.europe-west1.firebasedatabase.app",
  "projectId": "tg-recsys-bot",
  "storageBucket": "tg-recsys-bot.appspot.com",
  "messagingSenderId": "156859279337",
  "appId": "1:156859279337:web:968dd9bbfcbdd223080d78",
  "measurementId": "G-3TDY4N7RL1",
  "downloadTokens": None
}

REMOTE_PATH = "gallery/"
LOCAL_PATH = "/Users/aleksejshevcenko/Documents/BMSTU/Semester_6/TechAI/test/photos/"

app = pyrebase.initialize_app(config)

storage = app.storage()

# POST
def post_photo(local_path: str, url: str):
  url = url.split("/")[1]
  try:
    storage.child(REMOTE_PATH + url).put(local_path)
  except:
    print("ERROR: POST PHOTO")
    return None
  
  return "200"

# GET
def get_photo(save_local_path: str, from_url: str):
  try:
    storage.child(REMOTE_PATH + from_url).download(path=LOCAL_PATH, filename=save_local_path)
  except:
    print("ERROR: GET PHOTO")
    return None

  return "200"