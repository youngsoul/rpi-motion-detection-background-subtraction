from bs4 import BeautifulSoup


def read_pascal_voc_rectangles(pascal_voc_xml_path):
    motion_roi_rects = []

    if pascal_voc_xml_path is not None:
        soup = BeautifulSoup(open(pascal_voc_xml_path).read(), "lxml")
        boxes = soup.findAll('bndbox')

        for box in boxes:
            xmin = int(box.find("xmin").text)
            ymin = int(box.find("ymin").text)
            xmax = int(box.find("xmax").text)
            ymax = int(box.find("ymax").text)
            motion_roi_rects.append((xmin, ymin, xmax, ymax))

    return motion_roi_rects

def read_pascal_voc_data(pascal_voc_xml_path, normalize=False):
    bounding_boxes = []

    if pascal_voc_xml_path is not None:
        soup = BeautifulSoup(open(pascal_voc_xml_path).read(), "lxml")

        # get width and height
        width = int(soup.find('width').text)
        height = int(soup.find('height').text)

        objects = soup.findAll('object')

        for object in objects:
            name = object.find("name").text
            box = object.find("bndbox")
            xmin = int(box.find("xmin").text)
            ymin = int(box.find("ymin").text)
            xmax = int(box.find("xmax").text)
            ymax = int(box.find("ymax").text)

            if normalize:
                xmin = xmin/width
                xmax = xmax/width
                ymin = ymin/height
                ymax = ymax/height

            bounding_boxes.append((name, xmin, ymin, xmax, ymax))

    return bounding_boxes