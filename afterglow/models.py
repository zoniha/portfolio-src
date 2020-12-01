from django.db import models
from django.db import models
import tensorflow as tf
import numpy as np
import cv2
import io, base64
from PIL import Image


graph = tf.compat.v1.get_default_graph()


class Photo(models.Model):
    image = models.ImageField(upload_to='photos')

    IMAGE_SIZE = (64, 64)
    MIN_SIZE = (32, 32)
    MODEL_FILE_PATH = './afterglow/ml_models/afterglow.h5'
    name_dic = {
        'ran': (255, 0, 0),
        'moca': (152, 251, 152),
        'himari': (255, 182, 193),
        'tsugumi': (253, 253, 150),
        'tomoe': (128, 0, 128),
    }
    classes = [i for i in name_dic.keys()]

    def detect_main(self):
        model = None
        global graph
        with graph.as_default():
            model = tf.keras.models.load_model(self.MODEL_FILE_PATH)

            img_data = self.image.read()
            img_bin = io.BytesIO(img_data)
            img_pil = Image.open(img_bin)
            img_pil = img_pil.convert('RGB')
            image = np.asarray(img_pil)


            # 顔検出実行
            rec_image = self.detect_face(image, model)
            # cv2.imwrite('./afterglow/tmp/tmp.png', rec_image)
            rec_image = Image.fromarray(np.uint8(rec_image))
            # メモリ上への仮保管先を生成
            pred_bin = io.BytesIO()
            # pillowのImage.saveメソッドで仮保管先へ保存
            rec_image.save(pred_bin, format='PNG')
            # 保存したデータをbase64encodeメソッド読み込み
            # -> byte型からstr型に変換
            # -> 余分な区切り文字( ' )を削除
            b64_img = base64.b64encode(pred_bin.getvalue()).decode().replace("'", "")

            return b64_img

    def detect_face(self, image, model):
        img_gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        cascade_xml = './afterglow/cascade/lbpcascade_animeface.xml'
        cascade = cv2.CascadeClassifier(cascade_xml)

        # 顔検出の実行
        faces = cascade.detectMultiScale(img_gray, scaleFactor=1.11, minNeighbors=2, minSize=self.MIN_SIZE)

        if len(faces) > 0:
            for (x, y, w, h) in faces:
                face_img = image[y:y+h, x:x+w]
                face_img = cv2.resize(face_img, self.IMAGE_SIZE)
                # BGR->RGB変換、float型変換
                face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB).astype(np.float32)
                name, score = self.prediction(face_img, model)
                col = self.name_dic[name]
                # 認識結果を元画像に表示
                if score >= 0.60:
                    cv2.rectangle(image, (x, y), (x+w, y+h), col, 2)
                    cv2.putText(image, '%s:%d%%' % (name, score*100),
                                (x+10, y+h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)
                else:
                    cv2.rectangle(image, (x, y), (x+w, y+h), (192, 192, 192), 2)
                    cv2.putText(image, '%s:%d%%' % ('others', score*100),
                                (x+10, y+h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (192, 192, 192), 2)
        else:
            pass
        return image

    def prediction(self, x, model):
        # 画像データをテンソル整形
        x = np.expand_dims(x, axis=0)
        x = x / 255.0
        pred = model.predict(x)[0]

        # 確率が高い上位3キャラを出力
        num = 3
        top_indices = pred.argsort()[-num:][::-1]
        result = [(self.classes[i], pred[i]) for i in top_indices]

        # 1番予測確率が高いキャラ名を返す
        return result[0]

    def image_src(self, image):
        with self.image.open(image) as img:
            base64_img = base64.b64encode(img.read()).decode()

            return 'data:' + img.file.content_type + ';base64,' + base64_img
