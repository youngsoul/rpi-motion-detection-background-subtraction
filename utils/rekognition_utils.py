# https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/python/example_code/rekognition/rekognition_objects.py


class RekognitionFace:
    """Encapsulates an Amazon Rekognition face."""

    def __init__(self, face, timestamp=None):
        """
        Initializes the face object.

        :param face: Face data, in the format returned by Amazon Rekognition
                     functions.
        :param timestamp: The time when the face was detected, if the face was
                          detected in a video.
        """
        self.bounding_box = face.get('BoundingBox')
        self.confidence = face.get('Confidence')
        self.landmarks = face.get('Landmarks')
        self.pose = face.get('Pose')
        self.quality = face.get('Quality')
        age_range = face.get('AgeRange')
        if age_range is not None:
            self.age_range = (age_range.get('Low'), age_range.get('High'))
        else:
            self.age_range = None
        self.smile = face.get('Smile', {}).get('Value')
        self.eyeglasses = face.get('Eyeglasses', {}).get('Value')
        self.sunglasses = face.get('Sunglasses', {}).get('Value')
        self.gender = face.get('Gender', {}).get('Value', None)
        self.beard = face.get('Beard', {}).get('Value')
        self.mustache = face.get('Mustache', {}).get('Value')
        self.eyes_open = face.get('EyesOpen', {}).get('Value')
        self.mouth_open = face.get('MouthOpen', {}).get('Value')
        self.emotions = [emo.get('Type') for emo in face.get('Emotions', [])
                         if emo.get('Confidence', 0) > 50]
        self.face_id = face.get('FaceId')
        self.image_id = face.get('ImageId')
        self.timestamp = timestamp

    def to_dict(self):
        """
        Renders some of the face data to a dict.

        :return: A dict that contains the face data.
        """
        rendering = {}
        if self.bounding_box is not None:
            rendering['bounding_box'] = self.bounding_box
        if self.age_range is not None:
            rendering['age'] = f'{self.age_range[0]} - {self.age_range[1]}'
        if self.gender is not None:
            rendering['gender'] = self.gender
        if self.emotions:
            rendering['emotions'] = self.emotions
        if self.face_id is not None:
            rendering['face_id'] = self.face_id
        if self.image_id is not None:
            rendering['image_id'] = self.image_id
        if self.timestamp is not None:
            rendering['timestamp'] = self.timestamp
        has = []
        if self.smile:
            has.append('smile')
        if self.eyeglasses:
            has.append('eyeglasses')
        if self.sunglasses:
            has.append('sunglasses')
        if self.beard:
            has.append('beard')
        if self.mustache:
            has.append('mustache')
        if self.eyes_open:
            has.append('open eyes')
        if self.mouth_open:
            has.append('open mouth')
        if has:
            rendering['has'] = has
        return rendering

    def __str__(self):
        return f"{self.gender} {self.age_range} [{self.emotions}]"


class RekognitionText:
    """Encapsulates an Amazon Rekognition text element."""

    def __init__(self, text_data):
        """
        Initializes the text object.

        :param text_data: Text data, in the format returned by Amazon Rekognition
                          functions.
        """
        self.text = text_data.get('DetectedText')
        self.kind = text_data.get('Type')
        self.id = text_data.get('Id')
        self.parent_id = text_data.get('ParentId')
        self.confidence = text_data.get('Confidence')
        self.geometry = text_data.get('Geometry')

    def to_dict(self):
        """
        Renders some of the text data to a dict.

        :return: A dict that contains the text data.
        """
        rendering = {}
        if self.text is not None:
            rendering['text'] = self.text
        if self.kind is not None:
            rendering['kind'] = self.kind
        if self.geometry is not None:
            rendering['polygon'] = self.geometry.get('Polygon')
        return rendering

    def __str__(self):
        return f"{self.parent_id}<-{self.id}: '{self.text}' [{self.confidence} Type: {self.kind}]"


class RekognitionLabel:
    """Encapsulates an Amazon Rekognition label."""

    def __init__(self, label, timestamp=None):
        """
        Initializes the label object.

        :param label: Label data, in the format returned by Amazon Rekognition
                      functions.
        :param timestamp: The time when the label was detected, if the label
                          was detected in a video.
        """
        self.name = label.get('Name')
        self.confidence = label.get('Confidence')
        # Instances
        #   array of
        #       BoundingBox
        #           Width, Height, Left, Top in normalized values
        #       Confidence
        self.instances = label.get('Instances')
        self.parents = label.get('Parents')
        self.timestamp = timestamp

    def to_dict(self):
        """
        Renders some of the label data to a dict.

        :return: A dict that contains the label data.
        """
        rendering = {}
        if self.name is not None:
            rendering['name'] = self.name
        if self.timestamp is not None:
            rendering['timestamp'] = self.timestamp
        return rendering


def create_collection(collection_name, rekognition_client):
    response = rekognition_client.create_collection(CollectionId=collection_name)
    if response['StatusCode'] == 200:
        collection_arn = response['CollectionArn']
        return collection_arn
    else:
        raise Exception(f"Could not create collection with name: {collection_name}")


def delete_collection(collection_name, rekognition_client):
    response = rekognition_client.delete_collection(CollectionId=collection_name)
    if response['StatusCode'] == 200:
        return True
    else:
        raise Exception(f"Could not delete collection with name: {collection_name}")


def list_collections(rekognition_client):
    response = rekognition_client.list_collections()
    collections = response['CollectionIds']
    return collections


def register_face_in_collection(image_bytes, image_name, collection_name, rekognition_client):
    image_payload = {
        'Bytes': image_bytes
    }
    response = rekognition_client.index_faces(CollectionId=collection_name,
                                              Image=image_payload,
                                              ExternalImageId=image_name,
                                              QualityFilter='AUTO',
                                              DetectionAttributes=['ALL'])
    return response['FaceRecords']

def detect_face_in_collection(image_bytes, collection_name, rekognition_client):

    image_payload = {
        'Bytes': image_bytes
    }
    response = rekognition_client.search_faces_by_image(CollectionId=collection_name,
                                              Image=image_payload,
                                              MaxFaces=1,
                                              FaceMatchThreshold=90 )
    return response['FaceMatches']
