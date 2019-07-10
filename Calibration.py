
import cv2
import cv2.aruco as aruco

def is_grayscale_image(img):
	return len(img.shape) == 2

def is_color_image(img):
	return len(img.shape) > 2

def draw_detected_targets(target_img, corners, ids):
	d_i = cv2.imread(target_img, 1)
	draw_image = d_i.copy()
	cv2.aruco.drawDetectedMarkers(draw_image, corners, ids)
	resize = cv2.resize(draw_image, (2000, 1500), interpolation=cv2.INTER_LINEAR)
	cv2.imshow('frame', resize)

def filter_detected_targets_by_id(a,b,x):
	return [i for i,j in zip(a,b) if j == x]

def get_image_corners(target_img):

	img = cv2.imread(target_img, 0)
	aruco_img = img

	if is_color_image(img):
		aruco_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_250)
	corners, ids, rejected_img_points = aruco.detectMarkers(aruco_img, aruco_dict)

	# draw_detected_targets(target_img, corners, ids)

	target_matches = filter_detected_targets_by_id(corners, ids, 13)[0]
	single_target = target_matches[0]

	target_corner_ints = [[int(corner[0]), int(corner[1])] for corner in single_target]

	return target_corner_ints