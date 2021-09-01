"""Reconocimiento facial con OpenCV.

Permite la captura, el entrenamiento y el reconocimiento de rostros.

classes:
    Capture
    Recognize
    Train
    Helper
"""
import os
import cv2
from datetime import datetime
import numpy as np
from shutil import rmtree
from time import time
from smbus2 import SMBus
from mlx90614 import MLX90614


class Capture(object):
    """Detecta rostros en imágenes y los almacena en miniaturas.

    Crea la carpeta de salida, carga el clasificador y verifica su
    validez, intenta abrir la primera cámara.

    Args:
        id: Identificador de usuario.
        cap: Cámara para captura de video.

    Attributes:
        _face_classifier: Clasificador haarcascade de rostros.
        _eye_classifier: Clasificador haarcascade de ojos.
        _cap: Cámara para captura de video.
        _output: Directorio para guardar las minituras de los rostros.
        _count: Número de rostros detectados.
        is_face: ¿Hay un rostro en la imagen?.

    Methods:
        load
        _detect
        _save_thumb

    Raises:
        ValueError: Si no se cargó el clasificador.
        ValueError: Si no se encontró cámara.

    """

    _face_classifier = None
    _eye_classifier = None
    _cap = None
    _output = None
    _count = 0
    is_face = False

    def __init__(self, id, cap):
        self._output = 'data/' + id
        face_xml = 'models/haarcascade_frontalface_default.xml'
        eye_xml = 'models/haarcascade_eye.xml'
        if not os.path.isdir(self._output):
            os.mkdir(self._output)  # Crea la carpeta de salida
        self._face_classifier = cv2.CascadeClassifier(face_xml)
        if self._face_classifier.empty():
            raise ValueError(
                'Clasificador de rostro no encontrado: ' + face_xml)
        self._eye_classifier = cv2.CascadeClassifier(eye_xml)
        if self._eye_classifier.empty():
            raise ValueError(
                'Clasificador de ojos no encontrado: ' + eye_xml)
        self._cap = cap  # Primera cámara

    def load(self, detect=False):
        """Lee una imagen desde la cámara y detecta el primer rostro.

        Voltea la imagen leída para obtener el efecto espejo, gira 90 grados,
        si es necesario detecta el primer rostro y dibuja un rectángulo para
        ubicar los ojos.

        Args:
            detect: True o Flase, ¿Se intentará detectar rostros?.

        """
        self.is_face = False
        image = cv2.flip(self._cap.read()[1], 0)  # Voltear horizontalmente
        rotacion = cv2.getRotationMatrix2D((320, 320), 90, 1)
        image = cv2.warpAffine(image, rotacion, (480, 640))  # Rotar
        if detect:
            image = self._detect(image)
        # Rectángulo de los ojos
        cv2.rectangle(image, (110, 225), (370, 300), (0, 0, 255), 5)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # De BGR a RGB

    def _detect(self, image):
        """Detecta el primer rostro en una imagen.

        Crea una copia de la imagen para no modificar el original, en la
        imagen a escala de grises se detecta los rostros, al recorrer el
        primer rostro se dibuja un rectángulo para mostrar sus límites y
        su id, para luego guardar la miniatura.

        Args:
            image: Arreglo de imagen en la que se detectará rostros.

        Returns:
            Arreglo de imagen completa con los limites del rostro.

        """
        aux = image.copy()  # Imagen original
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # A grises
        faces = self._face_classifier.detectMultiScale(
            gray, scaleFactor=1.3, minNeighbors=5, minSize=(480, 480))
        for (x, y, w, h) in faces:
            eyes = self._eye_classifier.detectMultiScale(
                gray[225:300, 110:370], scaleFactor=1.7, minNeighbors=6)
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(image, (110 + ex, 225 + ey),
                              (110 + ex + ew, 225 + ey + eh),
                              (255, 255, 255), 2)
                self.is_face = True  # Encontró rostro y ojos
            if self.is_face:
                self._count += 1
                cv2.putText(image, str(self._count), (x, y - 10),
                            2, 2, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 1)
                self._save_thumb(aux[y:y + h, x:x + w])
            break
        return image

    def _save_thumb(self, image):
        """Guarda la miniatura de una imagen.

        Crea el directorio ‘folder’ si no existe, crea la miniatura de 150x150,
        genera un nombre y guarda la miniatura.

        Args:
            image: Arreglo que contiene el rostro detectado.
            folder: Directorio en que se guarda la miniatura.

        """
        image = cv2.resize(image, (150, 150))  # Reducir imagen
        now = datetime.now()  # Fecha actual para nombrar la miniatura
        name = [f'{self._output}/{now.year}-{now.month}-{now.day}_']
        name.append(f'{now.hour}-{now.minute}-{now.second}_{now.microsecond}')
        name.append('.jpg')
        cv2.imwrite(''.join(name), image)  # Guardar imagen


class Recognize(object):
    """"Reconoce rostros.

    Attributes:
        _face_classifier: Clasificador de rostro.
        _eye_classifier: Clasificador de ojos.
        _recognizer: Algoritmo de reconocimiento facial.
        cap: Cámara para la captura de imágenes.
        found_nose: ¿Se encontró nariz?
        found_face: ¿Se encontró rostro?
        face_of: Identificador de usuario al que pertenece el rostro.
        count: Contador de veces que se intentará reconocer un rostro.
        _temp: Temperatura registrada.
        _recog_time: Tiempo de reconocimiento.
        _gauge_time: Tiempo de toma de temperatura.
        _avg: Promedio de temperatura.

    Methods:
        load
        _detect
        _eye_search
        _nose_search
        _predict
        avg_temp
        recog_time
        gauge_time
        reset

    """
    _face_classifier = None
    _eye_classifier = None
    _recognizer = None
    cap = None
    found_nose = False
    found_face = False
    face_of = None
    count = 0
    _temp = []
    _recog_time = 0
    _gauge_time = 0
    _avg = 0

    def __init__(self):
        face_xml = 'models/haarcascade_frontalface_default.xml'
        eye_xml = 'models/haarcascade_eye.xml'
        nose_xml = 'models/haarcascade_mcs_nose.xml'
        model_xml = 'models/EigenFace.xml'
        self._face_classifier = cv2.CascadeClassifier(face_xml)
        if self._face_classifier.empty():
            raise ValueError(
                'Clasificador de rostro no encontrado: ' + face_xml)
        self._eye_classifier = cv2.CascadeClassifier(eye_xml)
        if self._eye_classifier.empty():
            raise ValueError(
                'Clasificador de ojos no encontrado: ' + eye_xml)
        self.nose_classifier = cv2.CascadeClassifier(nose_xml)
        if self.nose_classifier.empty():
            raise ValueError(
                'Clasificador de nariz no encontrado: ' + nose_xml)
        self._recognizer = cv2.face.EigenFaceRecognizer_create()
        self._recognizer.read(model_xml)
        if self._recognizer.empty():
            raise ValueError(
                'Modelo entrenado no encontrado: ' + model_xml)
        self.cap = cv2.VideoCapture(0)  # Primera cámara
        if not self.cap.isOpened():
            raise ValueError('Cámara no encontrada.')
        self.sensor = MLX90614(SMBus(1), address=0x5A)

    def load(self, detect=False):
        """Lee una imagen desde la cámara."""
        image = cv2.flip(self.cap.read()[1], 0)  # Voltear horizontalmente
        rotacion = cv2.getRotationMatrix2D((320, 320), 90, 1)
        image = cv2.warpAffine(image, rotacion, (480, 640))  # Rotar
        if detect:
            image = self._detect(image)
        # Rectángulo de los ojos
        cv2.rectangle(image, (110, 225), (370, 300), (0, 0, 255), 5)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # De BGR a RGB

    def _detect(self, image):
        """Detecta un rosotro en la imágen."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # A grises
        faces = self._face_classifier.detectMultiScale(
            gray, scaleFactor=1.3, minNeighbors=5, minSize=(480, 480))
        for (x, y, w, h) in faces:
            if self._recog_time == 0:
                self._recog_time = time()
                self._gauge_time = time()
            self._temp.append(self.sensor.get_object_1() + 10.68)
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 1)
            has_eye, image = self._eye_search(image, gray[225:300, 110:370])
            if has_eye:
                has_nose, image = self._nose_search(
                    image, gray[y + h // 2:y + h, x:x + w], x, y, h)
                if has_nose:
                    self.found_nose = True
                else:
                    self._predict(gray[y:y + h, x:x + w])
            break
        return image

    def _eye_search(self, image, roi):
        """Buscar ojos en el área de interés."""
        eyes = self._eye_classifier.detectMultiScale(
            roi, scaleFactor=1.7, minNeighbors=6)
        has_eye = False
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(image, (110 + ex, 225 + ey),
                          (110 + ex + ew, 225 + ey + eh),
                          (255, 255, 255), 1)
            has_eye = True
        return has_eye, image

    def _nose_search(self, image, roi, x, y, h):
        """Buscar nariz en el rostro."""
        noses = self.nose_classifier.detectMultiScale(
            roi, scaleFactor=1.7, minNeighbors=6, minSize=(60, 60))
        has_nose = False
        for (nx, ny, nw, nh) in noses:
            cv2.rectangle(image, (x + nx, y + ny + h // 2),
                          (x + nx + nw, y + ny + nh + h // 2),
                          (255, 255, 255), 1)
            has_nose = True
        return has_nose, image

    def _predict(self, roi):
        """Predecir el rostro encontrado."""
        image = cv2.resize(roi, (150, 150), interpolation=cv2.INTER_AREA)
        result = self._recognizer.predict(image)
        self.count += 1
        if result[1] < 4500:
            self.found_face = True
            self.face_of = result[0]
            self._recog_time = time() - self._recog_time

    def avg_temp(self):
        """Temperatura corporal."""
        if self._avg == 0:
            acum = 0
            for temp in self._temp:
                acum += temp
            acum = acum / len(self._temp)
            self._gauge_time = time() - self._gauge_time
            self._avg = round(acum, 2)
        return self._avg

    def recog_time(self):
        """Tiempo de reconocimiento de rostro."""
        return round(self._recog_time, 2) + 8

    def gauge_time(self):
        """Tiempo de toma de temperatura."""
        return round(self._gauge_time, 2) + 8

    def reset(self):
        """Reinicia el reconocimiento facial."""
        self.found_face = False
        self.found_nose = False
        self.face_of = None
        self.count = 0
        self._temp = []
        self._recog_time = 0
        self._gauge_time = 0
        self._avg = 0


class Train(object):
    """Entrena y alamcena los resultados en un archivo."""

    def __init__(self):
        labels = []
        data = []
        with os.scandir('data') as users:
            for user in users:
                if user.is_dir():
                    with os.scandir(user.path) as faces:
                        _label = int(user.name)
                        for face in faces:
                            if face.is_file() and face.path.endswith('.jpg'):
                                labels.append(_label)
                                data.append(cv2.imread(face.path, 0))

        face_recognizer = cv2.face.EigenFaceRecognizer_create()
        face_recognizer.train(data, np.array(labels))
        face_recognizer.write('models/EigenFace.xml')


class Helper(object):
    """Clase que nos ayudará en las diferentes clases.

    Methods:
        get_pics
        remove_file
        remove_dir
        set_date
        play

    """
    @staticmethod
    def get_pics(id):
        """Obtiene las rutas de las imágenes de un usuario."""
        pics = []
        with os.scandir('data/' + id) as files:
            for file in files:
                if file.is_file() and file.path.endswith('.jpg'):
                    pics.append(file.path)
        return pics

    @staticmethod
    def remove_file(path):
        """Elimina un archivo."""
        os.remove(path)

    @staticmethod
    def remove_dir(path):
        """Elimina un directorio, incluyendo archivos y subdirectorios."""
        rmtree(path)

    @staticmethod
    def set_date(cmd):
        """Establecer la fecha y hora de Raspberry Pi."""
        sudo_pass = 'rpi'
        os.system(f'echo "{sudo_pass}" | sudo -S "{cmd}"')

    @staticmethod
    def play(path):
        """Reproducir sonido en Raspberry Pi"""
        """winsound.PlaySound('sound/denegado.wav',
                               winsound.SND_FILENAME | winsound.SND_ASYNC)"""
        os.system(f'omxplayer -o local {path} &')
