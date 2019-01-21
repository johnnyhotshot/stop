import cv2
from threading import Thread

cam = cv2.VideoCapture(0)
width = 640
height = 480
cam.set(3,640)
cam.set(4,480)
comprWidth = 160
comprHeight = 120

avgImageCount = 2500

def getAverageImage(imageCount):
    pictures = []
    print("Collecting image input...")
    for i in range(imageCount):
        ret, frame = cam.read()
        pictures.append(frame)
    print("Averaging images...")
    total = pictures[0]
    for i in range(1,imageCount):
        total = cv2.addWeighted(total,(i/imageCount),pictures[i],1-(i/imageCount),0)
    return total

def getPercentChange(current, last):
    #(pixelchange / 255) / (len*wid)
    if len(current) != len(last) != height or len(current[0]) != len(last[0]) != width:
        print("getPercentChange - images correct size")
        return
    current = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
    last = cv2.cvtColor(last, cv2.COLOR_BGR2GRAY)
    toReturn = 0
    
    for y in range(height):
        for x in range(width):
            toReturn += (abs(int(current[y][x]) - int(last[y][x])) / 255) / (height*width)

    return toReturn

def imageHasPerson(background, image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.GaussianBlur(image, (5, 5), 0)
    imageDifference = cv2.absdiff(background, image)
    ret, imageDifference = cv2.threshold(imageDifference, 127, 255, cv2.THRESH_BINARY)
    imageDifference, contours = cv2.findContours(imageDifference,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    return contours is not None

class DisplayThread(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global frame
        global lastFrame

        while True:
            try:
                cv2.imshow("Current Frame", frame)
            except:
                pass
            cv2.imshow("Last Frame", lastFrame)
            
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

class ImageAveragingThread(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global frame
        global lastFrame

        while True:
            frame = getAverageImage(avgImageCount)
            print(getPercentChange(frame, lastFrame))

            lastFrame = frame
            
            
        
        cam.release()
        cv2.destroyAllWindows()

#lastFrame = getAverageImage(avgImageCount)
frame = []

display = DisplayThread()
#display.start()
average = ImageAveragingThread()
#average.start()

background = getAverageImage(30)
background = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)
background = cv2.GaussianBlur(background, (5, 5), 0)

while True:
    ret, frame = cam.read()

    print(imageHasPerson(background, frame))
    
    cv2.imshow("Camera", frame)
    cv2.waitKey(1)
    
