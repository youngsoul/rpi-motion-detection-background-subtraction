import cv2
from rekognition_utils import RekognitionLabel, RekognitionText
import numpy as np


def read_image(image_path):
    image_file = open(image_path, 'rb')
    image_bytes = image_file.read()
    # image_np is an image bugger
    image_np = np.frombuffer(image_bytes, np.uint8)
    cv2_image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)

    h, w, chans = cv2_image.shape

    return image_bytes, cv2_image, rgb_image, h, w

def read_image_as_byte_str(image_path, convert_bgr2rgb=True):
    # when using opencv to read an image
    # the image format will always be BGR
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"No image found at: {image_path}")

    img_str = cv2.imencode('.jpg', image)[1].tobytes()

    # use imdecode function to see exactly what is being sent
    # to rekognition
    # image2 = cv2.imdecode(np.asarray(bytearray(img_str), dtype='uint8'), cv2.IMREAD_COLOR)
    #
    # # display image
    # cv2.imshow("encode/decode", image2)
    # cv2.waitKey(0)

    if convert_bgr2rgb:
        # then convert the image, but not the img_str
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w, chans = image.shape

    return img_str, image, h, w


def draw_label_bounding_box(rekognition_label: RekognitionLabel, image, label_y_offset=20):
    if rekognition_label.instances is not None:
        for instance in rekognition_label.instances:
            if 'BoundingBox' in instance:
                bb = instance['BoundingBox']
                draw_bounding_box(bb, image, rekognition_label.name, label_y_offset)

    return


def draw_text_bounding_box(rekognition_text: RekognitionText, image):
    if rekognition_text.geometry is not None:
        if 'BoundingBox' in rekognition_text.geometry:
            bb = rekognition_text.geometry['BoundingBox']
            draw_bounding_box(bb, image, rekognition_text.text)

    return

def draw_bounding_box(bounding_box, image, label=None, label_y_offset=20):
    h, w, chan = image.shape
    x_txt = int(bounding_box['Left'] * w)
    y_txt = int(bounding_box['Top'] * h + bounding_box['Height'] * h)

    cv2.rectangle(image, (int(bounding_box['Left'] * w), int(bounding_box['Top'] * h)),
                  (int(bounding_box['Left'] * w + w * bounding_box['Width']), int(bounding_box['Top'] * h + bounding_box['Height'] * h)),
                  (0, 255, 0), 2)
    if label is not None:
        cv2.putText(image, label, (x_txt, y_txt + label_y_offset), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 0, 255), 2)


def blur_bounding_box(bounding_box, image):
    h, w, chan = image.shape

    # Create ROI coordinates
    topLeft = (int(bounding_box['Left'] * w), int(bounding_box['Top'] * h))
    bottomRight = (int(bounding_box['Left'] * w + w * bounding_box['Width']), int(bounding_box['Top'] * h + bounding_box['Height'] * h))
    x, y = topLeft[0], topLeft[1]
    w, h = bottomRight[0] - topLeft[0], bottomRight[1] - topLeft[1]

    # Grab ROI with Numpy slicing and blur
    ROI = image[y:y + h, x:x + w]
    blur = cv2.GaussianBlur(ROI, (51, 51), 0)

    # Insert ROI back into image
    image[y:y + h, x:x + w] = blur

