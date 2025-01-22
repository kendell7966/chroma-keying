##############################################################################
# 12/23/2024
# Kendell Cottam (kendellwc@protonmail.com)
# Course: Fundamentals of CV and IP
# Week 6
# Assignment 3 - Chroma Keying
#
# About this app:
# 1) Pick a background color: adjust the 'Pick Color' trackbar value to '1'
#    and click on the background.
# 2) Adjust the 'Tolerance' trackbar to increase the range of colors that
#    will be considered to be the background.
# 3) Use the 'Softness' trackbar to blur the edges of the mask.
# 4) I have provided 3 different methods to reduce the green hue from the
#    foreground. Use the 'DF Method' trackbar to select the defringe method.
#    Method 1: This is a naive implementation that simply adjusts the values
#              in the green color channel.
#    Method 2: This uses an implementation of a 'white balancing' method
#              for color cast.
#    Method 3: This uses another implementation of 'white balancing' that
#              uses a white patch of pixels from the image. You will see
#              a red square around the patch of pixels selected (manually)
#              in the image when this method is selected and turned on.
# 5) Use the 'Defringe' trackbar to adjust the level of defringment for
#    methods 1 and 2. For method 3 this trackbar only turns it on or off.
##############################################################################

import cv2
import numpy as np

window_name = "Chroma Keying"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, (960, 540))

controls_windows_name = "Controls"
cv2.namedWindow(controls_windows_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(controls_windows_name, (512, 448))

frame = []
frame_hsv = []
isSelectingColor = False
isColorSelected = False
pickedColor = (int(0),int(0),int(0))
pickedColorHsv = (0,0,0)
tolerance = 0
softness = 0
defringe = 0
defringe_method = 0
defringe_method_name = ['Naive (green channel adjustment)', 'Percentile White Balance (adjustable)', 'White Patch Balancing (not adjustable)']


def on_select_color_change(*args):
    global isSelectingColor
    global isColorSelected
    mode = args[0]
    if mode == 1:
        isSelectingColor = True
        isColorSelected = False
    if mode == 0:
        isSelectingColor = False
        if pickedColor[0] == 0 and pickedColor[1] == 0 and pickedColor[2] == 0:
            isColorSelected = False
        else:
            isColorSelected = True
    return


def on_tolerance_change(*args):
    global tolerance
    if not isColorSelected:
        return
    tolerance = int(args[0])
    return


def on_softness_change(*args):
    global softness
    if not isColorSelected:
        return
    softness = int(args[0])
    return


def on_defringe_method_change(*args):
    global defringe_method
    defringe_method = int(args[0])
    update_controls_window()
    return


def on_defringe_change(*args):
    global defringe
    defringe = int(args[0])
    update_controls_window()
    return


def update_controls_window():
    text_area = np.zeros((256,512,3), np.uint8)

    # Display the picked color
    pos1 = (128,4)
    pos2 = (256,35)
    cv2.putText(text_area, "Picked Color", (10,24), fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale = 0.5, color = (250, 250, 250), thickness = 1, lineType = cv2.LINE_AA)
    if isSelectingColor or isColorSelected:
        cv2.rectangle(img=text_area, pt1=pos1, pt2=pos2, color=pickedColor, thickness=-1, lineType=cv2.LINE_AA)
    else:
        cv2.rectangle(img=text_area, pt1=pos1, pt2=pos2, color=(255,255,255), thickness=1, lineType=cv2.LINE_AA)

    # Display defringe information
    text1 = "Defringe Method: " + defringe_method_name[defringe_method]
    if defringe_method == 1:
        text1 += "{}%".format(100.0 - (defringe / 4.0))
    cv2.putText(text_area, text1, (10, 64), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(250, 250, 250), thickness=1, lineType=cv2.LINE_AA)

    cv2.imshow(controls_windows_name, text_area)


def create_mask():
    lower = np.array([pickedColorHsv[0] - tolerance, 90, 90])
    upper = np.array([pickedColorHsv[0] + tolerance, 255, 255])
    background_mask = cv2.inRange(frame_hsv, lower, upper)

    # Soften the mask edges with blurring
    if softness > 0:
        ksize = softness * 2 + 1
        background_mask = cv2.GaussianBlur(background_mask, (ksize, ksize), 0)

    #cv2.imshow("mask", background_mask)
    return background_mask


def percentile_white_balance(image, percentile_value):
    # This method was adapted from code found at:
    # https://jmanansala.medium.com/image-processing-with-python-color-correction-using-white-balancing-6c6c749886de
    return (image * 1.0 / np.percentile(image, percentile_value, axis=(0, 1))).clip(0, 1)


def white_patch_balancing(image, from_row, from_column, row_width, column_width):
    # This method was adapted from code also found at:
    # https://jmanansala.medium.com/image-processing-with-python-color-correction-using-white-balancing-6c6c749886de
    # One drawback with this method is that a patch of white pixels must be manually identified from the image.
    if defringe == 0:
        return image
    image_patch = image[from_row:from_row + row_width, from_column:from_column + column_width]
    image_max = (image * 1.0 / image_patch.max(axis=(0, 1))).clip(0, 1)
    image_max = cv2.rectangle(image_max, (from_column,from_row), (from_column+column_width,from_row+row_width), (0,0,255), 1, cv2.LINE_AA)
    return image_max


def defringe_image(image):
    if defringe_method == 0:    # Naive implementation - green channel adjustment
        image[:, :, 1] -= defringe / 255.0
        return image

    if defringe_method == 1:
        image = percentile_white_balance(image, 100.0 - (defringe / 4.0))    # defringe value in 0.25 increments
        return image

    if defringe_method == 2:
        # Drawback with this method - location of patch of white pixels is identified manually and hard-coded here
        if defringe > 0:
            image = white_patch_balancing(image, 500, 730, 32, 32)
        return image


def handleMouse(action, x, y, flags, userdata):
    global pickedColor
    global pickedColorHsv

    if action == cv2.EVENT_LBUTTONDOWN:
        if isSelectingColor:
            pickedColorHsv = frame_hsv[y, x]
            current_color = frame[y, x]
            r = current_color[0]
            g = current_color[1]
            b = current_color[2]
            pickedColor = (int(r),int(g),int(b))
            update_controls_window()
            cv2.setTrackbarPos( "Pick Color", controls_windows_name, 0)


# Initialize the window containing the tracker bars
cv2.createTrackbar("Pick Color", controls_windows_name, 0, 1, on_select_color_change)
cv2.createTrackbar("Tolerance", controls_windows_name, 0, 50, on_tolerance_change)
cv2.createTrackbar("Softness", controls_windows_name, 0, 32, on_softness_change)
cv2.createTrackbar("DF Method", controls_windows_name, 0, 2, on_defringe_method_change)
cv2.createTrackbar("Defringe", controls_windows_name, 0, 32, on_defringe_change)
update_controls_window()

cv2.setMouseCallback(window_name, handleMouse)

# Foreground video
video = cv2.VideoCapture("greenscreen-demo.mp4")
if not video.isOpened():
    print("Error opening foreground video stream")

# Background video
stars = cv2.VideoCapture("starfield.mp4")
if not stars.isOpened():
    print("Error opening background video stream")

while video.isOpened() and stars.isOpened():

    ret, frame = video.read()
    ret2, frame_stars = stars.read()

    if not ret:
        # Reached the end of the foreground video, restart to the beginning
        video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = video.read()
    if not ret:
        print("Error reading foreground video stream")
        break

    if not ret2:
        # Reached the end of the background video, restart to the beginning
        stars.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret2, frame_stars = stars.read()
    if not ret2:
        print("Error reading background video stream")
        break

    frame = cv2.resize(frame, (960, 540))
    frame_stars = cv2.resize(frame_stars, (960, 540))
    frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    if not isColorSelected:
        cv2.imshow(window_name, frame)
    else:
        mask = create_mask()

        # Convert the images to float
        mask = np.float32(mask) / 255.0
        mask = cv2.merge([mask, mask, mask])    # Convert to 3 channels
        frame = np.float32(frame) / 255.0
        frame_stars = np.float32(frame_stars) / 255.0

        frame = defringe_image(frame)

        # Combine the foreground and background frames
        combined = frame * (1 - mask) + frame_stars * mask

        cv2.imshow(window_name, combined)

    key = cv2.waitKey(10)
    if key == 27:
        break

# Cleanup resources
stars.release()
video.release()
cv2.destroyAllWindows()
