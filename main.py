"""
Usage:

python main.py --video-file ./media/atv.mp4 --pascal-voc ./config/motion_roi.xml

python main.py --video-file ./media/walkers2.mp4 --pascal-voc ./config/motion_roi.xml

python main.py --video-file ./media/walkers2.mp4 --pascal-voc ./config/motion_roi.xml --slow-motion

python main.py --video-file ./media/walkers2.mp4 --pascal-voc ./config/motion_roi.xml --bg-config ./config/bg_subtraction_config.json




"""
import sys

from utils.BackgroundSubtractUtil import BackgroundSubtractor
from utils.conf import Conf
import cv2
import time
import argparse
import datetime
from pathlib import Path
from utils.pascal_voc_util import read_pascal_voc_rectangles
from utils.BackgroundImageWriterUtil import BackgroundImageWriter
from utils.DropboxFileWatcherUpload import DropboxFileWatcherUpload
from dotenv import load_dotenv
import os
from imutils.video import VideoStream

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg-config", required=False, default="./config/mac_bg_subtract_config.json", help="path to the background subtraction config json file")
    ap.add_argument("--slow-motion", action='store_true', help="When motion detected, slow down video")
    ap.add_argument("--wait-on-start", action='store_true', help="After showing the first frame, wait for a key to be pressed to continue")
    ap.add_argument("--video-file", required=False, help="Full path to video file to read from. If this is not set, then the Webcam will be used.")
    ap.add_argument("--video-dir", required=False, help="Full path to directory that contains video files. The directory and all subdirectories will be searched for video files")
    ap.add_argument("--pascal-voc", required=False, help="Path to rectangle annotated file in PascalVOC format with ROIs to look for motion")
    args = vars(ap.parse_args())

    conf = Conf(args['bg_config'])

    if conf['display_video']:
        original_window_name = 'Original'
        cv2.namedWindow(original_window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(original_window_name, 600, 600)
        cv2.moveWindow(original_window_name, 600, 100)

    if conf['display_mask']:
        subtractor_name = conf['named_subtractor']
        mask_window_name = f'{subtractor_name} Mask'
        cv2.namedWindow(mask_window_name, cv2.WINDOW_NORMAL)
        cv2.moveWindow(mask_window_name, 200, 250)

    # Determine if we are reading a video or using the computer camera
    video_files_to_process = []
    if args.get("video_file", None) != None:
        video_files_to_process.append(args['video_file'])
    elif args.get("video_dir", None) != None:
        path = Path(args.get("video_dir"))
        for p in path.rglob("*.MP4"):
            video_files_to_process.append(p.absolute())
    else:
        cap = VideoStream(usePiCamera=conf['picamera'], src=conf['camera_src']).start()
        time.sleep(2.0)

    # set this to a large value so the first frame is saved, i.e. greater than the
    # conf['frames_between_snaps'] value
    framesSinceSnap=10000
    snap_buffer = []

    # Bounding Boxes contains Regions of Interest
    # These bounding rectangles where created using LabelImg (pip install LabelImg )
    # and then using one of the jpgs in the motion directory.
    # Draw rectangles in the area that we are interested in looking for motion and save
    # file in the PascalVOC format.  An example file is in config/roi.xml
    # for the purpose of this example, I am just going to harvest the values and create the
    # rectangles.
    motion_roi_rects = []

    if args.get('pascal_voc', None) is not None:
        motion_roi_rects = read_pascal_voc_rectangles(args.get('pascal_voc'))

    bg_sub = BackgroundSubtractor(**conf.to_dict(), motion_roi_rects=motion_roi_rects)

    image_writer = BackgroundImageWriter(frames_between_writes=conf['frames_between_snaps'])
    image_writer.start()

    wait_on_start = args.get('wait_on_start', False)

    if conf["upload_dropbox"]:
        load_dotenv()
        env_path = conf['dropbox_env_file']
        load_dotenv(dotenv_path=env_path)
        access_token = os.getenv('dropbox_access_token')

        bg_dropbox = DropboxFileWatcherUpload(dropbox_access_token=access_token, root_dir=conf['detected_motion_dir'], pattern="*.jpg", delete_after_process=conf["delete_after_process"])
        bg_dropbox.start()

    frames_with_motion = 0
    total_frames = 0
    for i, vid in enumerate(video_files_to_process):
        print(f"Process file: {vid}.  {(i/len(video_files_to_process))*100:.1f} complete")

        cap = cv2.VideoCapture(str(vid))
        while True:
            rtn, frame = cap.read()
            if frame is None:
                break

            total_frames += 1

            # frame = imutils.resize(frame, width=800)
            original = frame.copy()

            # Draw the ROIs rectangles on the frame
            if args.get('pascal_voc') and conf['display_motion_roi']:
                for roi in motion_roi_rects:
                    cv2.rectangle(frame, (roi[0], roi[1]), (roi[2], roi[3]), (255, 255, 0), 2)

            timestamp = datetime.datetime.now()
            day_timestring = timestamp.strftime("%Y%m%d")
            hms_timestring = timestamp.strftime("%Y%m%d-%H%M%S.%f")[:-3]

            day_outputdir_path = f"{conf['detected_motion_dir']}/{day_timestring}"
            day_outputdir = Path(day_outputdir_path)

            day_outputdir.mkdir(parents=True, exist_ok=True)
            motionThisFrame, framesWithoutMotion, contours, frame, mask, mask_rect = bg_sub.apply(frame)

            if conf['log_motion_status']:
                if motionThisFrame:
                    print(f"Motion This Frame: {motionThisFrame}")

            if motionThisFrame:
                frames_with_motion += 1
                sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
                for contour in sorted_contours:
                    (rx, ry, rw, rh) = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh),(255, 0, 0), 2)

                if conf['write_snaps']:
                    image_filename = f"{hms_timestring}.jpg"
                    image_fqn = day_outputdir / image_filename
                    image_writer.add_image_to_queue(str(image_fqn), original)

            if conf['display_mask']:
                cv2.imshow(mask_window_name, mask)

            if conf['display_video']:
                cv2.imshow(original_window_name, frame)

            if conf['display_mask'] or conf['display_video']:
                key = cv2.waitKey(3) & 0xFF

                # if the `q` key was pressed, break from the loop
                if key == ord("q"):
                    break

                if wait_on_start == True:
                    cv2.waitKey(0)
                    wait_on_start = False

                if motionThisFrame and args['slow_motion'] == True:
                    time.sleep(0.2)

            print(f"Percentage of frames with motion: {(frames_with_motion/total_frames)*100:.2f}%")

            if cap != None:
                cap.release()

    image_writer.drain()

    if conf['display_mask'] or conf['display_video']:
        cv2.destroyAllWindows()

    if conf["upload_dropbox"]:
        bg_dropbox.drain()
