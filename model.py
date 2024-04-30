from deepface.DeepFace import verify, analyze, represent
import numpy as np
import pandas as pd
import datetime

from service import Service
from constants import ERRORS, RESPONSE


class Model:
    __instance = None

    __service = None
    __db = None

    __MODEL_NAME: str = "VGG-Face"
    __BACKEND: str = "yolov8"
    __METRICS: str = "cosine"

    __backends = ['opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface', 'mediapipe','yolov8','yunet','fastmtcnn']
    __models = [ "VGG-Face", "Facenet", "Facenet512", "OpenFace", "DeepFace", "DeepID", "ArcFace", "Dlib", "SFace"]
    __metrics = ["cosine", "euclidean", "euclidean_l2"]
    
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
 
        return cls.__instance
  
    def __init__(self, local_path="./photos/", firebase_path="gallery/"):
        self.__LOCAL_PATH = local_path
        self.__REMOTE_PATH = firebase_path

        self.__service = Service(path_storage_config="firebase_storage_config.json",
                                 local_path=self.__LOCAL_PATH,
                                 firebase_path=self.__REMOTE_PATH)

        self.__db = self.__prepare_data("database.csv")
    

    def __prepare_data(self, path_data_base="database.csv"):
        db_images_start = pd.read_csv(path_data_base)
        db_images_start = db_images_start.drop('Unnamed: 0', axis=1)

        result = db_images_start['vector'].apply(lambda x: np.array(list(map(float, (x[1:-2].split(", "))))))
        db_images_start.vector = result
        return db_images_start

    @staticmethod
    def cos(a, b):
        return a@b/((a**2).sum() * (b**2).sum())

    def find_photo(self, path: str) -> tuple:
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
            embedding_objs = represent(model_name=self.__MODEL_NAME, 
                      detector_backend=self.__BACKEND, 
                      img_path=path)
            embedding = embedding_objs[0]["embedding"]
            embedding = np.array(embedding)
        except Exception as e:
            print(ERRORS.MODEL["FindEmb"])
            return ('FIND', data, 'ERR')
    
        result = []

        try:
            for i in range(self.__db.shape[0]):
                row = self.__db.iloc[i]
                result.append([self.cos(embedding, row.vector), row.url])

            result = sorted(result, reverse=False)
            data = [result[-1], result[-2]]
        except Exception as e:
            print(ERRORS.MODEL["FindToBest"])
            return ('FIND', data, 'ERR')

        try:
            result_photo_1 = self.__service.get_photo(to_local_path=self.__LOCAL_PATH + data[0][1], from_url=data[0][1]) 
            result_photo_2 = self.__service.get_photo(to_local_path=self.__LOCAL_PATH + data[1][1], from_url=data[1][1])

            if (result_photo_1 == None) or (result_photo_2 == None):
                print(ERRORS.MODEL["FindNoneReturnPhoto"])
                return ('FIND', None, 'ERR')
        except Exception as e:
            print(ERRORS.MODEL["FindGet"])
            return ('FIND', None, 'ERR')

        return ('FIND', data, 'OK')

    def analysis_photo(self, path: str) -> tuple:
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
            print(ERRORS.MODEL["AnalEmb"])
            return ('ANLS', None, 'ERR')
    
        try:
            data = data[0]
            age = data['age']
            gender = data['dominant_gender']
            race = data['dominant_race']
            emotion = data['dominant_emotion']

            gender = RESPONSE.TRANSLATE[gender]
            race = RESPONSE.TRANSLATE[race]
            emotion = RESPONSE.TRANSLATE[emotion]

            data = f'Результат анализа\n возраст: {age}\n пол: {gender}\n национальность: {race}\n эмоция: {emotion}'
        except Exception as e:
            print(ERRORS.MODEL["AnalPars"])
            return ('ANLS', None, 'ERR')
    
        return ('ANLS', data, 'OK')

    def compare_photos(self, path1: str, path2: str) -> tuple:
        '''
        Метод верификации человека на двух фотографиях, отправленных пользователем.
        input:
            path: str - путь локального хранения фотографии, отправленной пользователем
        output:
            (type: str, data: str or None, status: str)
            data - строка с ответом и дополнительной информацией в необходимом формате, которую получит пользователь от бота.
        '''
        try:
            data = verify(img1_path=path1, img2_path=path2, detector_backend=self.__BACKEND)
        except Exception as e:
            print(ERRORS.MODEL["VerEmb"])
            return ('CMPR', None, 'ERR')

        try:
            verified = 'распознан ✅' if data['verified'] == True else 'разные люди ⛔'
            distance = data['distance']
            treshold_to_verify = data['threshold']
            model = data['model']
            similarity_metric = data['similarity_metric']

            data = f'Результат верификации\n схожесть: {verified}\n расстрояние: {distance}\n порог: {treshold_to_verify}\n модель: {model}\n метрика схожести: {similarity_metric}'
        except Exception as e:
            print(ERRORS.MODEL["VerPars"])
            return ('CMPR', None, 'ERR')
    
        return ('CMPR', data, 'OK')

    def add_photo(self, path: str) -> tuple:
        '''
        Метод добавления фотографии в общую базу данных.
        input:
            path: str - путь локального хранения фотографии, отправленной пользователем
        output:
            (type: str, data: str or None, status: str)
            data - строка с ответом о добавлении фотографии, которую получит пользователь от бота.
        '''
        list_of_paths = self.__db.path.to_list()

        if path.split("/")[1] in list_of_paths:
            print(ERRORS.MODEL["AddAlreadyExist"])
            data = 'Фотография не была добавлена, так как она уже есть в БД!'
            return ('ADD', data, 'OK')

        try:
            embedding_objs = represent(model_name=self.__MODEL_NAME, 
                      detector_backend=self.__BACKEND, 
                      img_path=path)
        except Exception as e:
            print(ERRORS.MODEL["AddEmb"])
            return ('ADD', None, 'ERR')

        try:
            messageTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            TimeStamp = str(messageTime)

            result_post_photo = self.__service.post_photo(from_local_path=path, to_url=path)
            
            if result_post_photo == None:
                print(ERRORS.MODEL["AddPost"])
                return ('ADD', None, 'ERR')
        except Exception as e:
            print(ERRORS.MODEL["AddPost"])
            return ('ADD', None, 'ERR')

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
            print(ERRORS.MODEL["AddDataSet"])
            return ('ADD', None, 'ERR: Добавление в dataset')
    
        try:
            self.__db = self.__prepare_data("database.csv")
        except Exception as e:
            print(ERRORS.MODEL["AddDataSet"])
            print(ERRORS.MODEL["AddUpdateDB"])
            data = 'Фотография не была добавлена\nЧто-то пошло не так.. 😔'
            return ('ADD', data, 'OK')

        data = 'Фотография добавлена в общую базу всех фотографий, спасибо! 🗃️'
        return ('ADD', data, 'OK')

