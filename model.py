from deepface.DeepFace import verify, analyze, represent
import numpy as np
import pandas as pd
import datetime

from service import post_photo, get_photo

backends = [
  'opencv', 
  'ssd', 
  'dlib', 
  'mtcnn', 
  'retinaface', 
  'mediapipe',
  'yolov8',
  'yunet',
  'fastmtcnn',
]

models = [
  "VGG-Face", 
  "Facenet", 
  "Facenet512", 
  "OpenFace", 
  "DeepFace", 
  "DeepID", 
  "ArcFace", 
  "Dlib", 
  "SFace",
]

metrics = ["cosine", "euclidean", "euclidean_l2"]

MODEL_NAME: str = "VGG-Face"
BACKEND: str = "yolov8"
METRICS: str = "cosine"
IMG_PATH: str = "gallery/1.jpg"
START_ID: int = -1

LOCAL_PATH_GALLERY: str = "photos/"


def prepare_data(data_base):
    database_images_start = pd.read_csv(data_base)
    database_images_start = database_images_start.drop('Unnamed: 0', axis=1)

    result = database_images_start['vector'].apply(lambda x: np.array(list(map(float, (x[1:-2].split(", "))))))
    database_images_start.vector = result
    return database_images_start

database_images = prepare_data("database.csv")

def cos(a, b):
    return a@b/((a**2).sum() * (b**2).sum())

def find_photo(path: str) -> tuple:
    '''
    Метод поиска двух фотографий, наиболее похожих на отправленную пользователем.
    input:
        path: str - путь локального хранения фотографии, отправленной пользователем
    output:
        (type: str, data: [str, str] or None, status: str)
        data - список локальных путей к двум фотографиям скаченным фотографиям.
    '''

    data = None

    try:
        embedding_objs = represent(model_name=MODEL_NAME, 
                      detector_backend=BACKEND, 
                      img_path=path)
        embedding = embedding_objs[0]["embedding"]
        embedding = np.array(embedding)
    except Exception as e:
        print("Получение эмбединга поиска")
        return ('FIND', data, 'ERR')
    
    result = []

    try:
        for i in range(database_images.shape[0]):
            row = database_images.iloc[i]
            result.append([cos(embedding, row.vector), row.url])

        result = sorted(result, reverse=False)
        data = [result[-1], result[-2]]
    except Exception as e:
        print("Поиск лучших двух фотографий")
        return ('FIND', data, 'ERR')

    try:
        result_photo_1 = get_photo(save_local_path=LOCAL_PATH_GALLERY + data[0][1], from_url=data[0][1]) 
        result_photo_2 = get_photo(save_local_path=LOCAL_PATH_GALLERY + data[1][1], from_url=data[1][1])

        if (result_photo_1 == None) or (result_photo_2 == None):
            return ('FIND', None, 'ERR')
    except Exception as e:
        print("Ошибка запроса GET")
        return ('FIND', None, 'ERR')

    return ('FIND', data, 'OK')

def analysis_photo(path: str) -> tuple:
    '''
    Метод анализа фотографии, возвращает возраст, пол, национальность и эмоцию.
    input:
        path: str - путь локального хранения фотографии, отправленной пользователем
    output:
        (type: str, data: str or None, status: str)
        data - строка с признаками в необходимом формате, которую получит пользователь от бота.
    '''
    try:
        data = analyze(img_path=path, actions=['age', 'gender', 'race', 'emotion'])
    except Exception as e:
        print("Работа метода анализа")
        return ('ANLS', None, 'ERR')
    
    try:
        data = data[0]
        age = data['age']
        gender = data['dominant_gender']
        race = data['dominant_race']
        emotion = data['dominant_emotion']

        data = f'Результат анализа\n возраст: {age}\n пол: {gender}\n национальность: {race}\n эмоция: {emotion}'
    except Exception as e:
        print("Парсинг джейсона анализа")
        return ('ANLS', None, 'ERR')
    
    return ('ANLS', data, 'OK')

def compare_photos(path1: str, path2: str) -> tuple:
    '''
    Метод верификации человека на двух фотографиях, отправленных пользователем.
    input:
        path: str - путь локального хранения фотографии, отправленной пользователем
    output:
        (type: str, data: str or None, status: str)
        data - строка с ответом и дополнительной информацией в необходимом формате, которую получит пользователь от бота.
    '''
    try:
        data = verify(img1_path=path1, img2_path=path2, detector_backend=BACKEND)
    except Exception as e:
        print("Работада метода верификации")
        return ('CMPR', None, 'ERR')

    try:
        verified = 'распознан ✅' if data['verified'] == True else 'разные люди ⛔'
        distance = data['distance']
        treshold_to_verify = data['threshold']
        model = data['model']
        similarity_metric = data['similarity_metric']

        data = f'Результат верификации\n схожесть: {verified}\n расстрояние: {distance}\n порог: {treshold_to_verify}\n модель: {model}\n метрика схожести: {similarity_metric}'
    except Exception as e:
        print("Парсинг джейсона анализа")
        return ('CMPR', None, 'ERR')
    
    return ('CMPR', data, 'OK')

def add_photo(path: str) -> tuple:
    '''
    Метод добавления фотографии в общую базу данных.
    input:
        path: str - путь локального хранения фотографии, отправленной пользователем
    output:
        (type: str, data: str or None, status: str)
        data - строка с ответом о добавлении фотографии, которую получит пользователь от бота.
    '''
    global database_images
    list_of_paths = database_images.path.to_list()

    if path.split("/")[1] in list_of_paths:
        print("Фотография уже есть в БД")
        data = 'Фотография не была добавлена, так как она уже есть в БД!'
        return ('ADD', data, 'OK')

    try:
        embedding_objs = represent(model_name=MODEL_NAME, 
                      detector_backend=BACKEND, 
                      img_path=path)
    except Exception as e:
        print("Получение эмбединга")
        return ('ADD', None, 'ERR: Получение эмбединга')
    
    print(path)
    try:
        messageTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        TimeStamp = str(messageTime)

        result_post_photo = post_photo(local_path=path, url=path)
        if result_post_photo == None:
           return ('ADD', None, 'ERR')
    except Exception as e:
        print("Отправка в БД")
        return ('ADD', None, 'ERR: Отправка в БД')

    try:
        dict = {
          'path': path.split("/")[1], 
          'vector': [embedding_objs[0]["embedding"]], 
          'dateTime': TimeStamp, 
          'url': path.split("/")[1]
        }
        new_image = pd.DataFrame({k: v for k, v in dict.items()})
        new_image.to_csv("new.csv")

        new_images = pd.read_csv("new.csv")
        database_img = pd.read_csv("database.csv")
        update_dataframe = pd.concat([database_img, new_images], ignore_index = True)
        update_dataframe.to_csv("database.csv")
    except Exception as e:
        print("Добавление в dataset")
        return ('ADD', None, 'ERR: Добавление в dataset')
    
    try:
        database_images = prepare_data("database.csv")
    except Exception as e:
        print("Обновление доступа к БД")
        data = 'Фотография не была добавлена\nЧто-то пошло не так.. 😔'
        return ('ADD', data, 'OK')

    data = 'Фотография добавлена в общую базу всех фотографий, спасибо! 🗃️'
    return ('ADD', data, 'OK')

