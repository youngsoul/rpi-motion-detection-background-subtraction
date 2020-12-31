import cv2
import numpy as np
import imutils


class BackgroundSubtractor():

    def __init__(self, named_subtractor='GMG', min_radius:int=0, min_area_ratio=0, annotate_background_motion=False, erode_kernel:int=0, erode_iterations:int=0,
                 dilate_kernel:int=0, dilate_iterations:int=0, **kwargs):
        """

        :param named_subtractor: one of CNT,GMG(DEFAULT),MOG,GSOC,LSBP
        :type named_subtractor:
        """
        self.OPENCV_BG_SUBTRACTORS = {
            "CNT": cv2.bgsegm.createBackgroundSubtractorCNT,
            "GMG": cv2.bgsegm.createBackgroundSubtractorGMG,
            "MOG": cv2.bgsegm.createBackgroundSubtractorMOG,
            "GSOC": cv2.bgsegm.createBackgroundSubtractorGSOC,
            "LSBP": cv2.bgsegm.createBackgroundSubtractorLSBP,
            "MOG2": cv2.createBackgroundSubtractorMOG2
        }

        subtractor_params = {}
        if f"{named_subtractor}_params" in kwargs.keys():
            subtractor_params = kwargs[f"{named_subtractor}_params"]

        self.subtractor = self.OPENCV_BG_SUBTRACTORS[named_subtractor](**subtractor_params)

        self.eKernel = None
        self.dKernel = None

        if erode_kernel > 0:
            self.erode_kernel = [erode_kernel, erode_kernel]
            self.erode_iterations = erode_iterations
            # create erosion kernels
            self.eKernel = np.ones(tuple(self.erode_kernel), "uint8")

        if dilate_kernel > 0:
            self.dilate_kernel = [dilate_kernel, dilate_kernel]
            self.dilate_iterations = dilate_iterations

            # create dilation kernels
            self.dKernel = np.ones(tuple(self.dilate_kernel), "uint8")

        self.min_radius = min_radius
        self.min_area_ratio = min_area_ratio

        self.framesWithoutMotion = 0

        self.annotate_image = annotate_background_motion


    def apply(self, image, motion_roi_rects=None):

        mask = None

        if motion_roi_rects is not None and len(motion_roi_rects) > 0:
            masked_frame = np.zeros(image.shape, dtype=np.uint8)
            for roi in motion_roi_rects:
                image_roi = image[roi[1]:roi[3], roi[0]:roi[2]]
                masked_frame[roi[1]:roi[3], roi[0]:roi[2]] = image_roi
            mask = self.subtractor.apply(masked_frame)
        else:
            mask = self.subtractor.apply(image)

        # perform erosions and dilations to eliminate noise and fill gaps
        if self.eKernel is not None:
            mask = cv2.erode(mask, self.eKernel,
                             iterations=self.erode_iterations)
        if self.dKernel is not None:
            mask = cv2.dilate(mask, self.dKernel,
                              iterations=self.dilate_iterations)

        # find contours in the mask and reset the motion status
        contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        motionThisFrame = False

        image_area = (image.shape[0] * image.shape[1])

        # loop over the contours
        threshold_met_contours = []

        # use these variables to find the largest rectangle surrounding the
        # motion
        (minX, minY) = (np.inf, np.inf)
        (maxX, maxY) = (-np.inf, -np.inf)

        for c in contours:
            # compute the bounding circle and rectangle for the contour
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            (rx, ry, rw, rh) = cv2.boundingRect(c)

            (minX, minY) = (min(minX, rx), min(minY, ry))
            (maxX, maxY) = (max(maxX, rx + rw), max(maxY, ry + rh))

            contour_area = rw * rh

            # convert floating point values to integers
            (x, y, radius) = [int(v) for v in (x, y, radius)]

            # only process motion contours above the specified size
            # print(radius, (contour_area / image_area))
            if radius >= self.min_radius or (contour_area / image_area) >= self.min_area_ratio:
                motionThisFrame = True
                self.framesWithoutMotion = 0
                threshold_met_contours.append(c)

                if self.annotate_image:
                    if radius >= self.min_radius:
                        cv2.circle(image, (x, y), radius, (0, 0, 255), 4)
                    if (contour_area / image_area) >= self.min_area_ratio:
                        # print("\t***MOTION")
                        cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh),
                                  (0, 255, 0), 2)

        if not motionThisFrame:
            self.framesWithoutMotion += 1

        return motionThisFrame, self.framesWithoutMotion, threshold_met_contours, image, mask, (minX, minY, maxX, maxY)
