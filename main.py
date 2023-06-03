import cv2
import time,  math, numpy as np
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
#cTime = 0
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
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
# 볼륨조절 인터페이스 가져옴
volume = cast(interface, POINTER(IAudioEndpointVolume))
# 가능한 볼륨의 범위 가져옴, 최소 볼륨, 최대 볼륨 및 볼륨 단계의 순서
volRange = volume.GetVolumeRange()   #(-63.5, 0.0, 0.5) min max

minVol = -63
maxVol = volRange[1]
print(volRange)
hmin = 50
hmax = 200
volBar = 400
volPer = 0
vol = 0
color = (0,215,255)
click = False

# 손가락 끝마디, 0행부터 엄지 검지 중지 약지 소지
tipIds = [4, 8, 12, 16, 20]
mode = ''
active = 0

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
        elif (fingers == [0, 1, 0, 0, 0] or fingers == [0, 1, 1, 0, 0]) & (active == 0 ):
            mode = 'Scroll'
            active = 1
        elif (fingers == [1, 1, 0, 0, 0] ) & (active == 0 ):
             mode = 'Volume'
             active = 1
        elif (fingers == [1 ,1 , 1, 1, 1] ) & (active == 0 ):
             mode = 'Cursor'
             active = 1

############# Scroll 👇👇👇👇##############
    if mode == 'Scroll':
        active = 1
     #   print(mode)
        putText(mode)
        # 스크롤 up down에서 up down에 씌울 하얀색 박스 생성
        cv2.rectangle(img, (200, 410), (245, 460), (255, 255, 255), cv2.FILLED)
        if len(lmList) != 0:
            if fingers == [0,1,0,0,0]:
              #print('up')
              #time.sleep(0.1)
                putText(mode = 'U', loc=(200, 455), color = (0, 255, 0))
                pyautogui.scroll(100)

            if fingers == [0,1,1,0,0]:
                #print('down')
              #  time.sleep(0.1)
                putText(mode = 'D', loc =  (200, 455), color = (0, 0, 255))
                pyautogui.scroll(-100)
            elif fingers == [0, 0, 0, 0, 0]:
                active = 0
                mode = 'N'
################# Volume 👇👇👇####################
    if mode == 'Volume':
        active = 1
       #print(mode)
        if len(lmList) != 0:
            if fingers[-1] == 1:
                active = 0
                mode = 'N'
                print(mode)
            else:
                # print(lmList[4], lmList[8])
                x1, y1 = lmList[4][1], lmList[4][2]
                x2, y2 = lmList[8][1], lmList[8][2]
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                cv2.circle(img, (x1, y1), 10, color, cv2.FILLED)
                cv2.circle(img, (x2, y2), 10, color, cv2.FILLED)
                cv2.line(img, (x1, y1), (x2, y2), color, 3)
                cv2.circle(img, (cx, cy), 8, color, cv2.FILLED)

                length = math.hypot(x2 - x1, y2 - y1)
                # print(length)

                # hand Range 50-300
                # Volume Range -65 - 0
                vol = np.interp(length, [hmin, hmax], [minVol, maxVol])
                # 딱히 필요 없는 코드
                volBar = np.interp(vol, [minVol, maxVol], [400, 150])
                volPer = np.interp(vol, [minVol, maxVol], [0, 100])
                #print(vol)
                volN = int(vol)
                if volN % 4 != 0:
                    volN = volN - volN % 4
                    if volN >= 0:
                        volN = 0
                    elif volN <= -64:
                        volN = -64
                    elif vol >= -11:
                        volN = vol

                # print(int(length), volN)
                volume.SetMasterVolumeLevel(vol, None)
                if length < 50:
                    cv2.circle(img, (cx, cy), 11, (0, 0, 255), cv2.FILLED)

                cv2.rectangle(img, (30, 150), (55, 400), (209, 206, 0), 3)
                cv2.rectangle(img, (30, int(volBar)), (55, 400), (215, 255, 127), cv2.FILLED)
                cv2.putText(img, f'{int(volPer)}%', (25, 430), cv2.FONT_HERSHEY_COMPLEX, 0.9, (209, 206, 0), 3)


#######################################################################
    if mode == 'Cursor':
        active = 1
        #print(mode)
        putText(mode)
        # 커서 박스 크기, 위치 조정
        cv2.rectangle(img, (frameR, frameR - 50), (wCam - frameR, hCam - frameR - 50), (255, 255, 255), 3)

        if fingers[1:] == [0,0,0,0]: #thumb excluded
            active = 0
            mode = 'N'
            print(mode)
        else:  # 박스 끝으로 손가락이 움직이면 화면 끝으로 움직이도록 수정함
            if len(lmList) != 0:
                x1, y1 = lmList[8][1], lmList[8][2]
                w, h = autopy.screen.size()
                X = int(np.interp(x1, [frameR, wCam - frameR], [0, w]))
                Y = int(np.interp(y1, [frameR - 50, hCam - frameR - 50], [0, h]))
                cv2.circle(img, (lmList[8][1], lmList[8][2]), 7, (255, 255, 255), cv2.FILLED)
                cv2.circle(img, (lmList[4][1], lmList[4][2]), 10, (0, 255, 0), cv2.FILLED)  # thumb

                # cv2.circle(img, (lmList[20][1], lmList[20][2]), 10, (0, 255, 0), cv2.FILLED) #새끼손가락

                if X % 2 != 0:
                    X = X - X % 2
                if Y % 2 != 0:
                    Y = Y - Y % 2
                print(w - X, Y)
                # autopy.mouse.move(w-X,Y)
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
                
                #  pyautogui.moveTo(X,Y)
                if fingers[0] == 0:
                    cv2.circle(img, (lmList[4][1], lmList[4][2]), 10, (0, 0, 255), cv2.FILLED)  # thumb
                    pyautogui.mouseDown()
                    click = True
                    putText('drag')
                else:
                    pyautogui.mouseUp()
                    

    cTime = time.time()
    fps = 1/((cTime + 0.01)-pTime)
    pTime = cTime

    cv2.putText(img,f'FPS:{int(fps)}',(480,50), cv2.FONT_ITALIC,1,(255,0,0),2)
    cv2.imshow('Hand LiveFeed',img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    def putText(mode,loc = (250, 450), color = (0, 255, 255)):
        cv2.putText(img, str(mode), loc, cv2.FONT_HERSHEY_COMPLEX_SMALL,
                    3, color, 3)