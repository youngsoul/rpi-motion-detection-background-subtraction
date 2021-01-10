import numpy as np


def mask_image_to_rectanges(image, list_of_rect_rois: list, background_color='black'):
    masked_frame = None

    if list_of_rect_rois is not None and len(list_of_rect_rois) > 0:
        if background_color == 'black':
            masked_frame = np.zeros(image.shape, dtype=np.uint8)
        elif background_color == 'white':
            masked_frame = np.ones(image.shape, dtype=np.uint8)
        else:
            raise ValueError("Invalid background_color option.  Only 'black' or 'white' allowed.")

        # for each of the roi rectangles, pull out that section of the image and add it to the masked_frame
        # image.
        for roi in list_of_rect_rois:
            image_roi = image[roi[1]:roi[3], roi[0]:roi[2]]
            masked_frame[roi[1]:roi[3], roi[0]:roi[2]] = image_roi

    return masked_frame


