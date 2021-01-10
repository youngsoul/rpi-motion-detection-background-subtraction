import queue
from threading import Thread
import time
import cv2


class BackgroundImageWriter:
    """
        Write images to specified fully qualified name as a background, asynchronous activity
    """

    def __init__(self, max_image_q_depth:int=50, frames_between_writes:int=1, empty_q_poll_wait:int=1):
        self.max_image_q_depth = max_image_q_depth
        self.recording = False
        self.thread = None
        self.Q = None
        self.frame_between_writes = frames_between_writes
        self.empty_q_poll_wait = empty_q_poll_wait
        self.frames_since_writing = 100000


    def add_image_to_queue(self, fqn, image):
        try:
            self.frames_since_writing += 1

            if self.frames_since_writing > self.frame_between_writes:
                self.Q.put_nowait((fqn, image))
                self.frames_since_writing = 0

        except queue.Full:
            print(f"Queue Full: {self.Q.qsize()}")

    def start(self):
        # indicate that we are recording, start the video writer,
        # and initialize the queue of frames that need to be written
        # to the video file
        self.recording = True
        self.Q = queue.Queue(maxsize=self.max_image_q_depth)

        # start a thread write frames to the video file
        self.thread = Thread(target=self._write, args=())
        self.thread.daemon = True
        self.thread.start()

    def _write(self):
        while True:
            # check to see if there are entries in the queue
            if not self.Q.empty():
                # grab the next frame in the queue and write it
                # to the video file
                fqn, frame = self.Q.get()
                cv2.imwrite(fqn, frame)

            # otherwise, the queue is empty, so sleep for a bit
            # so we don't waste CPU cycles
            else:
                # if we are done recording, exit the thread
                if not self.recording:
                    return

                time.sleep(self.empty_q_poll_wait)

    def drain(self):
        while not self.Q.empty():
            time.sleep(1)

        self.recording = False

    def queue_size(self):
        return self.Q.qsize()