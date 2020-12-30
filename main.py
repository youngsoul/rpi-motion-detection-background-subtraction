from BackgroundSubtractUtil import BackgroundSubtractor
from utils.conf import Conf
import cv2
import time
import argparse
import datetime
from pathlib import Path

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg-config", required=False, default="./config/bg_subtract_config.json", help="path to the background subtraction config json file")
    ap.add_argument("--slow-motion", action='store_true', help="When motion detected, slow down video")
    ap.add_argument("--video-file", required=True, help="Full path to video file")
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
    while True:
        ret, frame = cap.read()
        if frame is None:
            break

        original = frame.copy()

        timestamp = datetime.datetime.now()
        day_timestring = timestamp.strftime("%Y%m%d")
        hms_timestring = timestamp.strftime("%Y%m%d-%H%M%S.%f")[:-3]

        day_outputdir = Path() / conf['detected_motion_dir'] / day_timestring
        day_outputdir.mkdir(parents=True, exist_ok=True)

        motionThisFrame, framesWithoutMotion, contours, frame, mask, mask_rect = bg_sub.apply(frame)

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