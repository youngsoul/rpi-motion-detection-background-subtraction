import sys
sys.path.append("..")

from utils.BackgroundFileProcessor import BackgroundFileProcessor
from pathlib import Path
import boto3
from rekognition_utils import RekognitionLabel
from cv2_utils import read_image, draw_label_bounding_box
from typing import List


class AWSRekognitionFileWatcher(BackgroundFileProcessor):

    def __init__(self, label_filter: List, aws_profile_name: str, aws_region: str, root_dir: str, pattern: str = "*",
                 delete_after_process: bool = False, batch_size: int = 10, polling_time: int = 5,
                 output_dir: str = "../aws_output"):
        super().__init__(root_dir, pattern, delete_after_process, batch_size, polling_time)
        self.label_filter = label_filter
        self.output_dir = output_dir
        self.destination = Path(self.output_dir)

        session = boto3.Session(profile_name=aws_profile_name, region_name=aws_region)
        self.rekognition_client = session.client('rekognition')

    def process_file(self, absolute_file_path):
        print(absolute_file_path)
        image_path = Path(absolute_file_path)

        try:
            img_str, image, rgb_image, h, w = read_image(str(image_path))
            image_data = {'Bytes': img_str}
            response = self.rekognition_client.detect_labels(
                Image=image_data,
                MaxLabels=10,
                MinConfidence=80)
            labels = [RekognitionLabel(label) for label in response['Labels']]

            for label in labels:
                if label.name.lower() in self.label_filter:
                    print(f"{label.name} with confidence: {label.confidence}")
                    dest_image_dir = self.destination / str(absolute_file_path).split("/")[-1].split("-")[0]
                    dest_image_dir.mkdir(parents=True, exist_ok=True)
                    dest_image_path = dest_image_dir / str(absolute_file_path).split("/")[-1]
                    print(dest_image_path)

                    if not dest_image_path.exists():
                        image_path.replace(dest_image_path)

                    # break out this loop, once we find one label save it
                    # break

        except Exception as exc:
            pass


if __name__ == '__main__':
    from dotenv import load_dotenv
    import os

    load_dotenv()
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)

    aws_profile_name = os.getenv('aws_profile_name')
    aws_region = os.getenv('aws_region')

    db = AWSRekognitionFileWatcher(
        label_filter=['transportation', 'wheel', 'vehicle', 'person', 'atv', 'bike', 'bicycle', 'motorcycle'],
        aws_profile_name=aws_profile_name, aws_region=aws_region, root_dir="../motion", pattern="*.jpg",
        delete_after_process=True)

    db.start()

    db.drain()
