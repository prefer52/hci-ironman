import cv2
import numpy as np


def detect(img, cascade):
    rects = cascade.detectMultiScale(img, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30),
                                     flags=cv2.CASCADE_SCALE_IMAGE)
    if len(rects) == 0:
        return []
    rects[:, 2:] += rects[:, :2]
    return rects


# 그레이 스케일
# 히스토그램 평활화
# 얼굴 영역 추출
# 얼굴 영역 제거
def remove_face_area(img, cascade):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    rects = detect(gray, cascade)

    height, width = img.shape[:2]

    for x1, y1, x2, y2 in rects:
        cv2.rectangle(img, (x1 - 10, 0), (x2 + 10, height), (0, 0, 0), -1)

    return img


def make_mask_image(img_bgr):
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # img_h,img_s,img_v = cv.split(img_hsv)

    low = (0, 30, 0)
    high = (15, 255, 255)

    img_mask = cv2.inRange(img_hsv, low, high)
    return img_mask


def distance_between_two_points(start, end):
    x1, y1 = start
    x2, y2 = end

    return int(np.sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2)))


def calculate_angle(A, B):
    A_norm = np.linalg.norm(A)
    B_norm = np.linalg.norm(B)
    C = np.dot(A, B)

    angle = np.arccos(C / (A_norm * B_norm)) * 180 / np.pi
    return angle


def find_max_area(contours):
    max_contour = None
    max_area = -1

    for contour in contours:
        area = cv2.contourArea(contour)

        x, y, w, h = cv2.boundingRect(contour)

        if (w * h) * 0.4 > area:
            continue

        if w > h:
            continue

        if area > max_area:
            max_area = area
            max_contour = contour

    if max_area < 10000:
        max_area = -1

    return max_area, max_contour


def get_finger_position(max_contour, img_result, debug):
    points1 = []

    # STEP 6-1
    M = cv2.moments(max_contour)

    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])

    max_contour = cv2.approxPolyDP(max_contour, 0.02 * cv2.arcLength(max_contour, True), True)
    hull = cv2.convexHull(max_contour)

    for point in hull:
        if cy > point[0][1]:
            points1.append(tuple(point[0]))

    if debug:
        cv2.drawContours(img_result, [hull], 0, (0, 255, 0), 2)
        for point in points1:
            cv2.circle(img_result, tuple(point), 15, [0, 0, 0], -1)

    # STEP 6-2
    hull = cv2.convexHull(max_contour, returnPoints=False)
    defects = cv2.convexityDefects(max_contour, hull)

    if defects is None:
        return -1, None

    points2 = []
    for i in range(defects.shape[0]):
        s, e, f, d = defects[i, 0]
        start = tuple(max_contour[s][0])
        end = tuple(max_contour[e][0])
        far = tuple(max_contour[f][0])

        angle = calculate_angle(np.array(start) - np.array(far), np.array(end) - np.array(far))

        if angle < 90:
            if start[1] < cy:
                points2.append(start)

            if end[1] < cy:
                points2.append(end)

    if debug:
        cv2.drawContours(img_result, [max_contour], 0, (255, 0, 255), 2)
        for point in points2:
            cv2.circle(img_result, tuple(point), 20, [0, 255, 0], 5)

    # STEP 6-3
    points = points1 + points2
    points = list(set(points))

    # STEP 6-4
    new_points = []
    for p0 in points:

        i = -1
        for index, c0 in enumerate(max_contour):
            c0 = tuple(c0[0])

            if p0 == c0 or distance_between_two_points(p0, c0) < 20:
                i = index
                break

        if i >= 0:
            pre = i - 1
            if pre < 0:
                pre = max_contour[len(max_contour) - 1][0]
            else:
                pre = max_contour[i - 1][0]

            next = i + 1
            if next > len(max_contour) - 1:
                next = max_contour[0][0]
            else:
                next = max_contour[i + 1][0]

            if isinstance(pre, np.ndarray):
                pre = tuple(pre.tolist())
            if isinstance(next, np.ndarray):
                next = tuple(next.tolist())

            angle = calculate_angle(np.array(pre) - np.array(p0), np.array(next) - np.array(p0))

            if angle < 90:
                new_points.append(p0)

    return 1, new_points


def process(img_bgr, debug):
    img_result = img_bgr.copy()

    # 1. 얼굴 영역 제거 : 손 역역만 추출하기 위해
    img_bgr = remove_face_area(img_bgr, cascade)

    # 2. 손 영역을 인식하기 쉽게 hsv로 변환 후 이진화
    img_binary = make_mask_image(img_bgr)
    cv2.imshow("hsv", img_binary)

    # 3. close 연산을 수행하여 끊긴 부분 연결
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    img_binary = cv2.morphologyEx(img_binary, cv2.MORPH_CLOSE, kernel, 1)
    cv2.imshow("Binary", img_binary)

    # 4. findContours를 활용하여 손의 외곽선 검출
    contours, hierarchy = cv2.findContours(img_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


    if debug:
        for cnt in contours:
            cv2.drawContours(img_result, [cnt], 0, (255, 0, 0), 3)


    # 5. 검출된 외곽선 영역 중 가장 큰 영역을 찾음. - 얼굴 제외 했기 때문에 손이 검출됨
    max_area, max_contour = find_max_area(contours)

    if max_area == -1:
        return img_result

    if debug:
        cv2.drawContours(img_result, [max_contour], 0, (0, 0, 255), 3)



    # 6. 외각선에 대해 convex hull을 계산하여 선의 방향이 바뀌는 부분을 손가락 후보로 설정함
    # Convex hull은 초록색 선, 검은 색 원은 손가락 후보임
    # 손 가락이 하나여도 검출이 된다.
    # -> 단점은 손가락을 모두 구부려도 convex hull에서 외각선이 바뀌는 부분을 검출하기 때문에
    # 손가락이 아닌 부분에 대해서도 손가락 후보로 설정된다.
    ret, points = get_finger_position(max_contour, img_result, debug)


    # 7. 손으로 지정된 부분에 대해서 포인트 출력해준다.
    if ret > 0 and len(points) > 0:
        for point in points:
            cv2.circle(img_result, point, 10, (255, 0, 255), cv2.FILLED)

    return img_result


cascade = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")
cap = cv2.VideoCapture(0)

while True:

    ret, img = cap.read()

    if ret == False:
        break

    img_result = process(img, debug=False)

    key = cv2.waitKey(1)
    if key == 27:
        break

    cv2.imshow("Result", img_result)

cap.release()
cv2.destroyAllWindows()