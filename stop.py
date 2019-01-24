"""
    STOP: Shitpost Tracking Objective Photographer
    Watches whiteboards over time to catalog significant changes (takes pictures of what people do on the whiteboard)

    by: Johnny Puskar

    *** Sign my Packet :) ***
    
"""
import cv2
import time
from threading import Thread

"""
    Setting up camera - creating camera and camera size variables
"""
cam = cv2.VideoCapture(0)
width = 640
height = 480
cam.set(3,width)
cam.set(4,height)


"""
    Other global variables
     changeThreshold:  the percentage the image must have changed by to be significant enough to be recorded
     quitting:         boolean to quit program, if true then program loops in threads should stop
     nextImageID:      number appended to saved image file
     
     delayOver:        if the board delay has been run or not (will be False if a BoardCheckDelay thread is currently running)
"""
changeThreshold = 0.01
quitting = False
nextImageID = 0
delayOver = True

"""
    Config file variables (global but can be set through stop.cfg file, set to default values)
     picDelay:         amount of seconds in between each time the board is checked (in seconds)
     cameraName:       name added to photo files to differentiate them from others
"""
picDelay = 60
cameraName = "STOP-Camera"

def readConfig():
    global picDelay
    global cameraName
    try:
        config = open("stop.cfg","r")
    except:
        print("Config file not found. Using default values...")
        return
    for line in config:
        try:
            if line[0] == "#":
                pass
            elif line[:line.find("=")].strip() == "picDelay":
                picDelay = int(line[line.find("=")+1:])
            elif line[:line.find("=")].strip() == "cameraName":
                cameraName = line[line.find("=")+1:]
        except:
            pass
    config.close()

readConfig()

def getAverageImage(imageCount: int):
    """
        getAverageImage(int imageCount)
        @param imageCount = how many frames should the camera record to be averaged together, must be >= 1
        @return image = returns the image average of  'imageCount' frames recorded from the camera
    """
    # Returns None if imageCount is out of range
    if imageCount < 1:
        return None
    # Creating array for picture
    pictures = []
    # Add imageCount frames to pictures list
    for i in range(imageCount):
        ret, frame = cam.read()
        pictures.append(frame)
    # Create variable 'total' to return, initially set to the first image
    total = pictures[0]
    # Loop through any remaining images, averaging them together with cv2.addWeighted. Weight is calculated so each image ends up weighted equally
    for i in range(1,imageCount):
        total = cv2.addWeighted(total,(i/imageCount),pictures[i],1-(i/imageCount),0)
    # Return final average image
    return total

def getPercentChange(current: list, last: list):
    """
        getPercentChange(image current, image last)
        @param current = the current frame to see how much change has occured in
        @param last = the last frame to see how much change has occurred since
        @return float = range between 0 and 1, percent change between images

        A pixel can change by a maximum value of 255 (white to black/black to white), which is a 100% change for that pixel
        Each pixels change is an equal part of the total images change
          == sum of [ (change in pixel value / 255) / (length * width) ] for each pixel

        Only counts pixel change if it is greater than 5, any fluctuation under is disregarded
    """
    # Print out error message and return None if images are not equal size
    if len(current) != len(last) != height or len(current[0]) != len(last[0]) != width:
        print("getPercentChange - images incorrect size")
        return None
    # Convert to black and white for color management ease
    current = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
    last = cv2.cvtColor(last, cv2.COLOR_BGR2GRAY)
    # Initialize variable for sum of changes
    toReturn = 0
    # Loop through each pixel, add their percent change to the total (divided by the area of the image)
    for y in range(height):
        for x in range(width):
            change = abs(int(current[y][x]) - int(last[y][x]))
            if change > 3:
                toReturn += (change / 255) / (height*width)
    # Return total sum
    return toReturn
    

def imageHasPerson(background: list, image: list):
    """
        imageHasPerson(image background, image image)
        @param background = the background frame (unaltered)
        @param image = the current frame of the camera
        @return boolean = true or false depending on if a person (or large enough object) is in the image
    """
    # Convert image to black and white and blur it
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.GaussianBlur(image, (7, 7), 0)
    # Convert blackground to black and white and blur it
    background = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)
    background = cv2.GaussianBlur(background, (7, 7), 0)
    # Create a new image, which is the absolute difference between the background and the image
    #  - the lighter each pixel is in the image, the greater the difference between pixel in the two input images
    imageDifference = cv2.absdiff(background, image)
    # Threshold the difference image, which sets any value that is above 127 (midway point for pixels) to white, all others to black
    # Creates a black and white silhouette image, where white silhouettes represent objects in frame
    ret, imageDifference = cv2.threshold(imageDifference, 127, 255, cv2.THRESH_BINARY)
    # Find contours in the difference image (points along the edge of any white silhouettes / objects in frame)
    imageDifference, contours = cv2.findContours(imageDifference,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    # Checks if the contours list exists (if there is an object in frame)
    if contours is not None:
        # Checks the size of each contour box and returns true if it is above 6
        #  Note: 6 is a mostly arbritrary number picked from testing, seems to work well enough
        for i in range(len(contours)):
            if len(contours[i]) > 4:
                return True
    # Returns false if there is no contours list or if the contours are not large enough
    #  to matter (typically happens with larger drawings on whiteboard or items on marker tray)
    return False

def recordImage(image):
    """
        recordImage(image image)
        @param image = image to save to file
    """
    # Designate nextImageID to be the global variable
    global nextImageID
    # Write image to file with nextImageID in the file name
    cv2.imwrite("output/" + cameraName + "_" + str(nextImageID) + ".png", image)
    # Increment nextImageID for the next time
    nextImageID += 1

class DisplayThread(Thread):
    """
        Thread class for displaying what the camera sees
        Used mostly for testing
    """
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        # Desigate quitting as the global variable
        global quitting
        while True:
            # Get current camera frame
            ret, frame = cam.read()
            # Show frame in window
            cv2.imshow("Current Frame", frame)
            # If q key is pressed, break from loop
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        # Sets quitting to true to end other threads
        quitting = True
        # Release camera and close windows
        cam.release()
        cv2.destroyAllWindows()

class BoardChangeDetectionThread(Thread):
    """
        Thread class for detecting change on the board and recording it
    """
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        # Designates global variables
        global background
        global quitting
        
        # Run until global quitting bool has been set to true (allows quitting from other threads)
        while not quitting:
            if delayOver:
                # Creates new delay thread to manage the delay before then next board check
                delay = BoardCheckDelay()
                delay.start()
                # Get current camera data
                ret, frame = cam.read()
                # If the image doesn't contain a person or object blocking the board, continue. Otherwise - current frame data goes unused
                if not imageHasPerson(background.copy(), frame.copy()):
                    # Get the percent change between the current frame and the last recorded frame
                    change = getPercentChange(frame, background)
                    print(change)
                    # Checks if the change between the two frames is considered significant
                    if change > changeThreshold:
                        print("[ ] == Recording new board! - " + str(time.time()))
                        # Save current frame to file
                        recordImage(frame)
                        # Set the background to the current frame
                        background = frame
                    else:
                        print("[XXX] == Not enough change for new board")
                else:
                    print("[X] == Tried to record, but a person was in the way!")
                

class BoardCheckDelay(Thread):
    """
        Thread class for managing delay between images
        (used instead of time.sleep() so that board analysis runtime isn't included in delay)

        Uses global picDelay variable for timing and sets global delayOver boolean
    """
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        # Designating global variables
        global picDelay
        global delayOver
        # Setting delayOver to False while the delay runs
        delayOver = False
        print("Running delay...")
        # Using for loop to calculate delay in second increments to allow for quitting mid-delay
        for i in range(picDelay):
            # Sleep for one second
            time.sleep(1)
            # Break out of loop early if thread is quitting
            if quitting:
                break
        # Set delayOver to True
        delayOver = True
        

# Get the average over one second to set as the current background frame
ret, background = cam.read()
# Record the background
recordImage(background)

"""
    Starting threads
    DisplayThread active for testing purposes
"""
display = DisplayThread()
display.start()
average = BoardChangeDetectionThread()
average.start()
    
