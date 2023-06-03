import cv2
import math, numpy as np
import HandTrackingModule as htm
import pyautogui, autopy
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

wCam, hCam = 640, 480
cap = cv2.VideoCapture(0)
cap.set(3,wCam) # 3은 width
cap.set(4,hCam) # 4는 height
pTime = 0
frameR = 100

# maxhands는 인식할 수 있는 손의 개수
# detectionicon은 노이즈에도 상관없이 얼마나 손을 잘 인식하나
# trackCon은 얼마나 손의 움직임을 잘 추적하나
# detectioncon과 trackcon은 크면 클수로 시스템 부하 증가
# 손 인식 떨림 방지를 위해 매개변수 값 조정 기존값 detectionCon = 0.85, trackCon = 0.8
detector = htm.handDetector(maxHands=1, detectionCon=0.5, trackCon=0.5)

# 스피커 장치에 대한 정보 가져옴
devices = AudioUtilities.GetSpeakers()
# 스피커 장치 활성화
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
# 볼륨조절 인터페이스 가져옴
volume = cast(interface, POINTER(IAudioEndpointVolume))
# 가능한 볼륨의 범위 가져옴, 최소 볼륨, 최대 볼륨 및 볼륨 단계의 순서
volRange = volume.GetVolumeRange()   #(-63.5, 0.0, 0.5) min max

minVol = -63
maxVol = volRange[1]
hmin = 50
hmax = 200
volBar = 400
volPer = 0
vol = 0
color = (0,215,255)

# 손가락 끝마디, 0행부터 엄지 검지 중지 약지 소지
tipIds = [4, 8, 12, 16, 20]
mode = ''
active = 0
w, h = autopy.screen.size()


def calculate_location(x1, y1, lmList):
    X = int(np.interp(x1, [frameR, wCam - frameR], [0, w]))
    Y = int(np.interp(y1, [frameR - 50, hCam - frameR - 50], [0, h]))

    cv2.circle(img, (lmList[8][1], lmList[8][2]), 7, (255, 255, 255), cv2.FILLED)
    cv2.circle(img, (lmList[12][1], lmList[12][2]), 10, (0, 255, 0), cv2.FILLED)  # thumb

    if X % 2 != 0:
        X = X - X % 2
    if Y % 2 != 0:
        Y = Y - Y % 2

    return X, Y


# PyAutoGUI의 FAILSAFE 모드 비활성화, 기본적으로 마우스가 왼쪽 상단 모서리로 이동하여
# 예기치 못한 오류를 방지하는 모드로 이를 비활성화하여 커서 이동x
pyautogui.FAILSAFE = False
while True:
    # success는 성공적으로 프레임을 읽어왔는지 여부 저장
    success, img = cap.read()
    img = cv2.flip(img, 1)
    # 손을 찾아서 이미지에 다시 할당
    img = detector.findHands(img)
    # 손의 특정 포인트(랜드마크)를 찾는다. draw=false를 하면 랜드마크를 그리지 않음
    # 랜드마크 위치는 손가락 동작 인식에 사용
    lmList = detector.findPosition(img, draw=False)
    #print(lmList)
    fingers = []

    if len(lmList) != 0:

        #Thumb
        # 손바닥이 보일때와 등이 보일때 동일하도록 설정
        # 두 경우는 x좌표가 서로 반전되므로 이를 전처리
        if lmList[tipIds[0]][1] > lmList[tipIds[-1]][1]:
            if lmList[tipIds[0]][1] >= lmList[tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        elif lmList[tipIds[0]][1] < lmList[tipIds[-1]][1]:
            if lmList[tipIds[0]][1] <= lmList[tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        for id in range(1,5):
            if lmList[tipIds[id]][2] < lmList[tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

      #  print(fingers)
        if (fingers == [0,0,0,0,0]) & (active == 0 ):
            mode='N'
        elif (fingers == [1, 1, 1, 1, 1]) & (active == 0):
            mode = 'Scroll'
            active = 1
        elif (fingers == [0, 1, 0, 0, 0] or fingers == [0, 1, 1, 0, 0]) & (active == 0):
             mode = 'Cursor'
             active = 1
        elif (fingers == [1, 1, 0, 0, 0] ) & (active == 0 ):
             mode = 'Volume'
             active = 1

    if mode == 'Scroll':
        active = 1
        putText(mode)
        # 스크롤 up down에서 up down에 씌울 하얀색 박스 생성
        cv2.rectangle(img, (200, 410), (245, 460), (255, 255, 255), cv2.FILLED)
        if len(lmList) != 0:
            if fingers == [1, 1, 1, 1, 1]:
                putText(mode = 'U', loc=(200, 455), color = (0, 255, 0))
                pyautogui.scroll(100)

            if fingers == [1, 0, 0, 0, 0]:
                putText(mode = 'D', loc =  (200, 455), color = (0, 0, 255))
                pyautogui.scroll(-100)
            elif fingers == [0, 0, 0, 0, 0]:
                active = 0
                mode = 'N'

    if mode == 'Volume':
        active = 1
        if len(lmList) != 0:
            if fingers[-1] == 1:
                active = 0
                mode = 'N'
            else:
                # Volume Range -65 - 0
                if fingers == [1, 0, 0, 0, 0]:
                    vol -= 1
                    if vol < -65:
                        vol = -65
                elif fingers == [0, 1, 0, 0, 0]:
                    vol += 1
                    if vol > 0:
                        vol = 0

                # 딱히 필요 없는 코드
                volBar = np.interp(vol, [minVol, maxVol], [400, 150])
                volPer = np.interp(vol, [minVol, maxVol], [0, 100])

                volume.SetMasterVolumeLevel(vol, None)

                cv2.rectangle(img, (30, 150), (55, 400), (209, 206, 0), 3)
                cv2.rectangle(img, (30, int(volBar)), (55, 400), (215, 255, 127), cv2.FILLED)
                cv2.putText(img, f'{int(volPer)}%', (25, 430), cv2.FONT_HERSHEY_COMPLEX, 0.9, (209, 206, 0), 3)

    if mode == 'Cursor':
        active = 1
        putText(mode)
        # 커서 박스 크기, 위치 조정
        cv2.rectangle(img, (frameR, frameR - 50), (wCam - frameR, hCam - frameR - 50), (255, 255, 255), 3)

        if fingers != [0, 1, 0, 0, 0] and fingers != [0, 1, 1, 0, 0]:
            active = 0
            mode = 'N'
        else:  # 박스 끝으로 손가락이 움직이면 화면 끝으로 움직이도록 수정함
            if len(lmList) != 0:
                x1, y1 = lmList[8][1], lmList[8][2]

                if fingers[1] == 1 and fingers[2] == 0:
                    X, Y = calculate_location(x1, y1, lmList)
                    
                    # 손가락이 박스 바깥으로 나가면 발생하던 out of range 에러 예외처리
                    try:
                        autopy.mouse.move(X, Y)
                    except:
                        if X > w - 1 and Y > h - 1:
                            autopy.mouse.move(w - 1, h - 1)
                        elif X > w - 1:
                            autopy.mouse.move(w - 1, Y)
                        elif Y > h - 1:
                            autopy.mouse.move(X, h - 1)

                if fingers[1] == 1 and fingers[2] == 1:
                    length, img, lineInfo = detector.findDistance(8, 12, img)
                    if length < 40:
                        cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                        pyautogui.mouseDown()
                        X, Y = calculate_location(x1, y1, lmList)
                        autopy.mouse.move(X, Y)
                    else:
                        pyautogui.mouseUp()
                    
                    
    cv2.imshow('Hand LiveFeed',img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    def putText(mode,loc = (250, 450), color = (0, 255, 255)):
        cv2.putText(img, str(mode), loc, cv2.FONT_HERSHEY_COMPLEX_SMALL,
                    3, color, 3)