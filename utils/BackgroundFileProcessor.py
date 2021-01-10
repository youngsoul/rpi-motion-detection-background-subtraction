from threading import Thread
import time
from pathlib import Path
import abc

class BackgroundFileProcessor:

    def __init__(self, root_dir: str, pattern:str="*", delete_after_process: bool=False, batch_size: int=10, polling_time: int=5 ):
        self.pattern = pattern
        self.delete_after_process = delete_after_process
        self.batch_size = batch_size
        self.polling_time = polling_time
        self.root_dir = root_dir

    def start(self):

        # start a thread write frames to the video file
        self.thread = Thread(target=self._run, args=())
        self.thread.daemon = True
        self.thread.start()

    def _run(self):

        while True:
            time.sleep(self.polling_time)
            path = Path(self.root_dir)
            for i, path_element in enumerate(path.rglob(self.pattern)):
                # path_name = str(path_element)
                if i >= self.batch_size:
                    break

                try:
                    file_path = path_element.absolute()
                    self.process_file(file_path)
                    if self.delete_after_process:
                        print(f"deleting....{file_path}")
                        Path(file_path).unlink()
                except Exception as exc:
                    print(exc)

    def drain(self):
        print(f"Drain: {self.root_dir}")
        while True:
            path = Path(self.root_dir)
            # gets all the files
            f = [y for y in path.rglob(self.pattern)]
            if len(f) == 0:
                break

            time.sleep(1)





    def join(self):
        self.thread.join()

    @abc.abstractmethod
    def process_file(self, absolute_file_path):
        raise NotImplementedError


if __name__ == '__main__':
    b = BackgroundFileProcessor(root_dir="./motion", pattern="*.jpg")

    b.start()

    b.join()
