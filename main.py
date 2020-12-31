"""
Usage:

python main.py --video-file ./media/atv.mp4

python main.py --video-file ./media/walkers2.mp4 --pascal-voc ./config/motion_roi.xml

python main.py --video-file ./media/walkers2.mp4 --pascal-voc ./config/motion_roi.xml --slow-motion

python main.py --video-file ./media/walkers2.mp4 --pascal-voc ./config/motion_roi.xml --bg-config ./config/bg_subtraction_config.json




"""
from BackgroundSubtractUtil import BackgroundSubtractor
from utils.conf import Conf
import cv2
import time
import argparse
import datetime
from pathlib import Path
from bs4 import BeautifulSoup


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg-config", required=False, default="./config/bg_subtract_config.json", help="path to the background subtraction config json file")
    ap.add_argument("--slow-motion", action='store_true', help="When motion detected, slow down video")
    ap.add_argument("--video-file", required=True, help="Full path to video file")
    ap.add_argument("--pascal-voc", required=False, help="Path to rectangle annotated file in PascalVOC format with ROIs to look for mation")
    args = vars(ap.parse_args())

    conf = Conf(args['bg_config'])

    bg_sub = BackgroundSubtractor(**conf.to_dict())

    original_window_name = 'Original'
    cv2.namedWindow(original_window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(original_window_name, 600, 600)
    cv2.moveWindow(original_window_name, 600, 100)

    subtractor_name = conf['named_subtractor']
    mask_window_name = f'{subtractor_name} Mask'
    cv2.namedWindow(mask_window_name, cv2.WINDOW_NORMAL)
    cv2.moveWindow(mask_window_name, 200, 250)

    cap = cv2.VideoCapture(args['video_file'])
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
        soup = BeautifulSoup(open(args.get('pascal_voc')).read(), "lxml")
        boxes = soup.findAll('bndbox')

        for box in boxes:
            xmin = int(box.find("xmin").text)
            ymin = int(box.find("ymin").text)
            xmax = int(box.find("xmax").text)
            ymax = int(box.find("ymax").text)
            motion_roi_rects.append((xmin,ymin,xmax, ymax))

    while True:
        ret, frame = cap.read()
        if frame is None:
            break

        # frame = imutils.resize(frame, width=800)
        original = frame.copy()

        # Draw the ROIs rectangles on the frame
        if args.get('pascal_voc') and conf['display_motion_roi']:
            for roi in motion_roi_rects:
                cv2.rectangle(frame, (roi[0], roi[1]), (roi[2], roi[3]), (255, 255, 0), 2)

        timestamp = datetime.datetime.now()
        day_timestring = timestamp.strftime("%Y%m%d")
        hms_timestring = timestamp.strftime("%Y%m%d-%H%M%S.%f")[:-3]

        day_outputdir = Path() / conf['detected_motion_dir'] / day_timestring
        day_outputdir.mkdir(parents=True, exist_ok=True)

        motionThisFrame, framesWithoutMotion, contours, frame, mask, mask_rect = bg_sub.apply(frame, motion_roi_rects=motion_roi_rects)

        if motionThisFrame:
            sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
            for contour in sorted_contours:
                (rx, ry, rw, rh) = cv2.boundingRect(contour)
                cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh),(255, 0, 0), 2)

            if conf['write_snaps']:
                framesSinceSnap += 1
                if framesSinceSnap >= conf['frames_between_snaps']:
                    image_filename = f"{hms_timestring}.jpg"
                    snapPath = day_outputdir / image_filename
                    snap_buffer.append( (str(snapPath), original))
                    framesSinceSnap=0

        if framesWithoutMotion > 24 and len(snap_buffer) > 0:
            for snap in snap_buffer:
                cv2.imwrite(snap[0], snap[1])
            snap_buffer = []

        cv2.imshow(mask_window_name, mask)

        cv2.imshow(original_window_name, frame)

        key = cv2.waitKey(3) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break

        if motionThisFrame and args['slow_motion'] == True:
            time.sleep(0.5)

    if len(snap_buffer) > 0:
        for snap in snap_buffer:
            cv2.imwrite(snap[0], snap[1])
        snap_buffer = []

    cap.release()
    cv2.destroyAllWindows()