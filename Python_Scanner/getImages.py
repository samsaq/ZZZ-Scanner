import math
import os
import sys
import pyautogui
import logging
from keyboard import press
from multiprocessing import Queue


# screen resolutions supported enum
class ScreenResolution:
    RES_1440P = (2560, 1440)
    RES_1080P = (1920, 1080)


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def setup_logging(log_file_path):
    logging.basicConfig(
        level=logging.DEBUG,
        filename=log_file_path,
        filemode="w",
        format="%(asctime)s - %(message)s",
    )


# Get the screen resolution
screenWidth, screenHeight = pyautogui.size()

# get the screen resolution enum
screenResolution = (
    ScreenResolution.RES_1440P if screenWidth == 2560 else ScreenResolution.RES_1080P
)


def switchToZZZ():
    """
    Switch to the Zenless Zone Zero game window
    """
    logging.info("Switching to ZenlessZoneZero")
    ZZZWindow = pyautogui.getWindowsWithTitle("ZenlessZoneZero")[0]
    if ZZZWindow.isActive == False:
        pyautogui.press(
            "altleft"
        )  # Somehow this is needed to switch to the window, Why though?
        ZZZWindow.activate()
    logging.info("Switched to ZenlessZoneZero")


def getToEquipmentScreen(queue: Queue, pageLoadTime):
    """
    Get to the equipment screen from the character screen

    Args:
        queue (Queue): Queue to send screenshots to for processing. Defaults to None. Also used to signal the end of the image collection via error message
        pageLoadTime (float): The time to wait for the page to load
    """
    logging.info("Getting to the equipment screen")
    # press c to get to the character screen
    press("c")
    logging.info("Pressed c for character screen")
    # wait for the character screen to load
    pyautogui.sleep(pageLoadTime)
    # adjust the target based on devMode
    target = "./Target_Images/zzz-equipment-button.png"

    # if the screen resolution is 1080p, we need to adjust the target
    if screenResolution == ScreenResolution.RES_1080P:
        target = "./Target_Images/zzz-equipment-button-1080p.png"

    # press the equipment button to get to the equipment screen
    try:
        equipmentButton = pyautogui.locateOnScreen(target, confidence=0.8)
    except Exception as e:
        logging.error(f"Error locating equipment button:  + {e}")
        logging.error(f"Current directory: {os.getcwd()}")
    logging.info("Located equipment button: " + str(equipmentButton))
    if equipmentButton == None:
        logging.error("Equipment button not found")
        print("Equipment button not found")
        queue.put(
            "Error - failed to get to the equipment screen"
        )  # cause the process to end early
        sys.exit(1)
    pyautogui.click(equipmentButton)
    # wait for the equipment screen to load
    pyautogui.sleep(pageLoadTime)


def getXYOfCircleEdge(centerX, centerY, radius, angle):
    x = centerX + radius * math.cos(math.radians(angle))
    y = centerY + radius * math.sin(math.radians(angle))
    return x, y


def selectParition(diskNumber):
    diskradius = 0.25 * screenHeight
    diskCoreCenter = (0.75 * screenWidth, screenHeight / 2)

    # move the mouse to the center Y and the right side of the screen (75%)
    pyautogui.moveTo(diskCoreCenter)

    match diskNumber:
        case 1:
            # move the disk at 225 degrees (disk 1)
            x, y = getXYOfCircleEdge(
                diskCoreCenter[0], diskCoreCenter[1], diskradius, 225
            )
            pyautogui.moveTo(x, y)
        case 2:
            # move the disk at 180 degrees (disk 2)
            x, y = getXYOfCircleEdge(
                diskCoreCenter[0], diskCoreCenter[1], diskradius, 180
            )
            pyautogui.moveTo(x, y)
        case 3:
            # move the disk at 135 degrees (disk 3)
            x, y = getXYOfCircleEdge(
                diskCoreCenter[0], diskCoreCenter[1], diskradius, 135
            )
            pyautogui.moveTo(x, y)
        case 4:
            # move to the disk at 45 degrees (disk 4)
            x, y = getXYOfCircleEdge(
                diskCoreCenter[0], diskCoreCenter[1], diskradius, 45
            )
            pyautogui.moveTo(x, y)
        case 5:
            # move to the disk at 0 degrees (disk 5)
            x, y = getXYOfCircleEdge(
                diskCoreCenter[0], diskCoreCenter[1], diskradius, 0
            )
            pyautogui.moveTo(x, y)
        case 6:
            # move to the disk at 315 degrees (disk 6)
            x, y = getXYOfCircleEdge(
                diskCoreCenter[0], diskCoreCenter[1], diskradius, 315
            )
            pyautogui.moveTo(x, y)
    pyautogui.click()


def scanPartition(partitionNumber, queue: Queue, discScanTime):
    startPosition = (0.075 * screenWidth, 0.15 * screenHeight)  # start top left
    distanceBetwenColumns = 0.07 * screenWidth
    distanceBetwenRows = 0.158
    columnNumber = 4
    rowNumber = 5
    endOfDiskDrives = scanForEndOfDiskDrives(distanceBetwenRows)

    pyautogui.moveTo(startPosition)

    # loop through this row of disk drives
    # if the end of the disk drives is visible, we'll need to figure out which of the 4 columns is the last one
    # and only continue down the row until we reach the last column with a disk drive

    curRowStart = startPosition
    scanNumber = 1
    while True:  # Changed to infinite loop with explicit break
        scanNumber = scanRow(
            columnNumber,
            curRowStart,
            distanceBetwenColumns,
            partitionNumber,
            queue,
            discScanTime,
            scanNumber,
        )

        endOfDiskDrives = scanForEndOfDiskDrives(distanceBetwenRows)
        if endOfDiskDrives:
            break  # Exit after scanning the row where we found the end

        pyautogui.scroll(-1)

    # for loop for the remaining rows on the final page of disk drives
    for i in range(2, rowNumber + 1):
        curRowStart = (
            curRowStart[0],
            curRowStart[1] + distanceBetwenRows * screenHeight,
        )
        endOfDiskDrives = False
        scanNumber = scanRowUntilEndOfDiskDrives(
            columnNumber,
            i,
            curRowStart,
            distanceBetwenColumns,
            distanceBetwenRows,
            partitionNumber,
            queue,
            discScanTime,
            scanNumber,
        )


def scanRow(
    columns,
    rowStartPosition,
    distanceBetwenColumns,
    partitionNumber,
    queue: Queue,
    discScanTime,
    scanNumber=1,
):
    # pyautogui.click()
    for i in range(1, columns + 1):
        x = rowStartPosition[0] + (i - 1) * distanceBetwenColumns
        y = rowStartPosition[1]
        pyautogui.moveTo(x, y)
        pyautogui.click()
        scanNumber = scanDiskDrive(partitionNumber, queue, discScanTime, scanNumber)
    return scanNumber


# a version of scanRow that uses endOfDiskDrives to determine when to stop
# used on rows 2-5 on the final page of disk drives
def scanRowUntilEndOfDiskDrives(
    columns,
    rowNum,
    rowStartPosition,
    distanceBetwenColumns,
    distanceBetwenRows,
    partitionNumber,
    queue: Queue,
    discScanTime,
    scanNumber=1,
):
    # check the current row for the end of disk drives
    endOfDiskDrives = scanForEndOfDiskDrives(distanceBetwenRows, rowNum)
    # pyautogui.click()
    for i in range(1, columns + 1):
        x = rowStartPosition[0] + (i - 1) * distanceBetwenColumns
        y = rowStartPosition[1]
        # check if the x is past or at the end of the disk drives
        # if so, break the loop
        if endOfDiskDrives != False and x >= endOfDiskDrives[0]:
            break
        pyautogui.moveTo(x, y)
        pyautogui.click()
        scanNumber = scanDiskDrive(partitionNumber, queue, discScanTime, scanNumber)
    return scanNumber


def scanForEndOfDiskDrives(distanceBetwenRows, rowNumber=None):

    if rowNumber == None:
        try:
            target = "./Target_Images/zzz-no-disk-drive-icon.png"
            if screenResolution == ScreenResolution.RES_1080P:
                target = "./Target_Images/zzz-no-disk-drive-icon-1080p.png"
            endOfDiskDrivesIcon = pyautogui.locateOnScreen(
                target,
                confidence=0.8,
            )
        except:
            endOfDiskDrivesIcon = False

        try:
            target = "./Target_Images/zzz-no-disk-drive-scrollbar.png"
            if screenResolution == ScreenResolution.RES_1080P:
                target = "./Target_Images/zzz-no-disk-drive-scrollbar-1080p.png"
            endOfDiskDrivesScrollbar = pyautogui.locateOnScreen(
                target,
                confidence=0.95,
            )
        except:
            endOfDiskDrivesScrollbar = False
        # return false if both the icon and the scrollbar are not visible
        if endOfDiskDrivesIcon == False and endOfDiskDrivesScrollbar == False:
            return False
        # else, return the one that is not false
        if endOfDiskDrivesIcon != False:
            return endOfDiskDrivesIcon
        return endOfDiskDrivesScrollbar

    rowModifier = 0.1 + (distanceBetwenRows * (rowNumber - 1))

    # check if the end of the disk drives is visible
    endOfDiskDrives = False
    try:
        target = "./Target_Images/zzz-no-disk-drive-icon.png"
        if screenResolution == ScreenResolution.RES_1080P:
            target = "./Target_Images/zzz-no-disk-drive-icon-1080p.png"
        endOfDiskDrives = pyautogui.locateOnScreen(
            target,
            confidence=0.8,
            region=(
                int(0.04 * screenWidth),  # left
                int(rowModifier * screenHeight),  # top
                int(0.275 * screenWidth),  # width
                int(0.125 * screenHeight),  # height
            ),
        )
    except:
        endOfDiskDrives = False
    return endOfDiskDrives


def testSnapshot(distanceBetwenRows, rowNumber):
    rowModifier = 0.1 + (distanceBetwenRows * (rowNumber - 1))
    screenshot = pyautogui.screenshot(
        region=(
            int(0.04 * screenWidth),  # left
            int(rowModifier * screenHeight),  # top
            int(0.275 * screenWidth),  # width
            int(0.125 * screenHeight),  # height
        )
    )
    screenshot.save("DiskDriveImages/test" + str(rowNumber) + ".png")


def scanDiskDrive(paritionNumber, queue: Queue, discScanTime, scanNumber=1):
    # get a screenshot of the disk drive after waiting for it to load, save it to a file
    pyautogui.sleep(discScanTime)
    screenshot = pyautogui.screenshot(
        region=(
            int(0.31 * screenWidth),  # left
            int(0.1 * screenHeight),  # top
            int(0.2 * screenWidth),  # width
            int(0.55 * screenHeight),  # height
        )
    )
    # save with partition number and scan number
    save_path = (
        "./scan_input/Partition"
        + str(paritionNumber)
        + "Scan"
        + str(scanNumber)
        + ".png"
    )
    screenshot.save(save_path)
    # put the image path in the queue
    queue.put(save_path)
    return scanNumber + 1


# WEngine specific functions


def switchToWEngineBackpack(pageLoadTime, pressTime=0.15):
    """
    Switch to the WEngine backpack view from open world traversal (no menu)

    Args:
        pageLoadTime (float): The time to wait for the page to load
        pressTime (float, optional): The time to hold the keypress. Defaults to 0.15.
    """
    logging.info("Opening the backpack")
    pyautogui.keyDown("b")
    pyautogui.sleep(pressTime)
    pyautogui.keyUp("b")
    pyautogui.sleep(pageLoadTime)
    logging.info("Arrived at WEngine backpack view")


def switchToWEngineBackpackFromDisks(pageLoadTime, pressTime=0.15):
    """
    Switch to the WEngine backpack view from the disk drive view (within character screen, with a partition selected)

    Args:
        pageLoadTime (float): The time to wait for the page to load
        pressTime (float, optional): The time to hold the keypress. Defaults to 0.15.
    """
    logging.info("Switching to the WEngine tab in the Backpack")

    logging.info("Exiting from the disk drive view")
    pyautogui.keyDown("esc")
    pyautogui.sleep(pressTime)
    pyautogui.keyUp("esc")
    pyautogui.sleep(pageLoadTime)

    logging.info("Exiting parition view")
    pyautogui.keyDown("esc")
    pyautogui.sleep(pressTime)
    pyautogui.keyUp("esc")
    pyautogui.sleep(pageLoadTime)

    logging.info("Exiting character screen")
    pyautogui.keyDown("esc")
    pyautogui.sleep(pressTime)
    pyautogui.keyUp("esc")
    pyautogui.sleep(pageLoadTime)

    logging.info("Entering Backpack (default tab is WEngine)")
    pyautogui.keyDown("b")
    pyautogui.sleep(pressTime)
    pyautogui.keyUp("b")
    pyautogui.sleep(pageLoadTime)

    logging.info("Arrived at WEngine backpack view")


def getWEngine(queue: Queue = None, outputFile="TestImages/test.png"):
    """
    Screenshot the WEngine item and save it to a file

    Args:
        outputFile (str, optional): The path to save the screenshot to. Defaults to "TestImages/test.png". Will create the directory if it doesn't exist.
    """
    targetDir = outputFile.split("/")[0]
    if targetDir and not os.path.exists(targetDir):
        os.makedirs(targetDir, exist_ok=True)
    screenshot = pyautogui.screenshot(
        region=(
            int(0.73 * screenWidth),  # left
            int(0.18 * screenHeight),  # top
            int(0.23 * screenWidth),  # width
            int(0.175 * screenHeight),  # height
        )
    )
    screenshot.save(outputFile)
    if queue:
        queue.put(outputFile)


# scan the WEngine tab in the backpack
def getWEngineTab(
    queue: Queue = None, scanTime: float = 0.25, save_folder: str = "scan_input"
):
    """
    Scans the WEngine tab in the backpack, either sending screenshots to a queue or saving to a folder for examination.

    Args:
        queue (Queue, optional): Queue to send screenshots to for processing. Defaults to None.
        scanTime (float, optional): Time to wait between scans. Defaults to 0.25.
        save_folder (str, optional): Folder to save screenshots to. Defaults to "scan_input". Will create the directory if it doesn't exist.

    Returns:
        int: The number of items scanned
        None: If an error occurs

    Raises:
        ValueError: If neither a queue nor save_folder is provided
    """
    if save_folder and not os.path.exists(save_folder):
        os.makedirs(save_folder)

    if not queue and not save_folder:
        raise ValueError("Must provide either a queue or save_folder or both")

    startPosition = (0.13 * screenWidth, 0.27 * screenHeight)  # start top left
    distanceBetweenColumns = 0.075 * screenWidth
    distanceBetweenRows = 0.165 * screenHeight
    columnNumber = 8  # vertical columns in the backpack
    rowNumber = 5  # rows per page

    pyautogui.moveTo(startPosition)

    curRowStart = startPosition
    scanNumber = 1

    while True:  # Scroll through pages until we hit the end
        # Scan current row
        for col in range(columnNumber):
            currentPos = (
                curRowStart[0] + (col * distanceBetweenColumns),
                curRowStart[1],
            )
            pyautogui.moveTo(currentPos)
            pyautogui.click()
            pyautogui.sleep(scanTime)

            # Take screenshot of the WEngine item
            if save_folder:
                getWEngine(
                    queue, os.path.join(save_folder, f"wengine_{scanNumber}.png")
                )
            else:
                getWEngine(f"TestImages/temp_{scanNumber}.png")
                os.remove(f"TestImages/temp_{scanNumber}.png")

            scanNumber += 1

        # Check if we've reached the end of the inventory
        try:
            target = "./Target_Images/zzz-inventory-end-scrollbar-1440p.png"
            if screenResolution == ScreenResolution.RES_1080P:
                target = "./Target_Images/zzz-inventory-end-scrollbar-1080p.png"
            endOfInventory = pyautogui.locateOnScreen(
                target,
                confidence=0.95,
            )
            if endOfInventory:
                break
        except:
            pass

        # Scroll down for next row
        pyautogui.scroll(-1)
        pyautogui.sleep(scanTime)

    # Scan remaining rows on the final page
    for row in range(1, rowNumber):
        curRowStart = (
            startPosition[0],
            startPosition[1] + (row) * distanceBetweenRows,
        )

        # For each column in the row
        for col in range(columnNumber):
            currentPos = (
                curRowStart[0] + (col * distanceBetweenColumns),
                curRowStart[1],
            )

            # Check for empty slot
            try:
                target = "./Target_Images/zzz-no-inventory-item-icon-1440p.png"
                if screenResolution == ScreenResolution.RES_1080P:
                    target = "./Target_Images/zzz-no-inventory-item-icon-1080p.png"
                emptySlot = pyautogui.locateOnScreen(
                    target,
                    confidence=0.9,
                    region=(
                        int(currentPos[0] - 0.08 * screenWidth),
                        int(currentPos[1] - 0.08 * screenHeight),
                        int(0.16 * screenWidth),
                        int(0.16 * screenHeight),
                    ),
                )
                if emptySlot:
                    return (
                        scanNumber - 1
                    )  # Exit  if we find an empty slot since we've reached the end of the inventory
            except Exception as e:
                pass

            # Take screenshot if not empty
            pyautogui.moveTo(currentPos)
            pyautogui.click()
            pyautogui.sleep(scanTime)

            if save_folder:
                getWEngine(
                    queue, os.path.join(save_folder, f"wengine_{scanNumber}.png")
                )
            else:
                getWEngine(f"TestImages/temp_{scanNumber}.png")
                with open(f"TestImages/temp_{scanNumber}.png", "rb") as f:
                    queue.put((scanNumber, f.read()))
                os.remove(f"TestImages/temp_{scanNumber}.png")

            scanNumber += 1

    return scanNumber - 1  # Return total number of items scanned


# the main function that will be called to get the images by the orchestrator
def getImages(queue: Queue, pageLoadTime, discScanTime, scantype):
    """
    Get the images for the specified type of scan

    Args:
        queue (Queue): Queue to send screenshots to for processing. Also used to signal the end and start of the image collection of each category & by error
        pageLoadTime (float): The time to wait for the page to load
        discScanTime (float): The time to wait between scans of the disk drives
        scantype (str): The type of scan to perform. Can be "all", "wengine", "character", "disk"
    """
    log_file_path = resource_path("scan_output/templog.txt")
    setup_logging(log_file_path)
    switchToZZZ()
    if scantype == "Disk":
        getToEquipmentScreen(queue, pageLoadTime)
        queue.put("Disk")
        # go through the 6 partitions
        for i in range(1, 7):
            selectParition(i)
            scanPartition(i, queue, discScanTime)
    elif scantype == "WEngine":
        switchToWEngineBackpack(pageLoadTime)
        queue.put("WEngine")
        getWEngineTab(queue, discScanTime)
    elif scantype == "Character":
        getToEquipmentScreen(queue, pageLoadTime)
        queue.put("Character")
        # TODO: implement character scan
    elif scantype == "All":
        # get the disk data
        getToEquipmentScreen(queue, pageLoadTime)
        queue.put("Disk")
        # go through the 6 partitions
        for i in range(1, 7):
            selectParition(i)
            scanPartition(i, queue, discScanTime)
        # get the wengine data
        queue.put("WEngine")
        switchToWEngineBackpackFromDisks(pageLoadTime)
        getWEngineTab(queue, discScanTime)
        # get the character data
        queue.put("Character")
        # TODO: implement character scan
    # put a message in the queue to signal the end of the image collection
    queue.put("Done")


# a test function to run the getImages function
if __name__ == "__main__":

    # set the working directory to the directory of the script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Create scan_output directory if it doesn't exist
    os.makedirs("scan_output", exist_ok=True)

    # remove the templog.txt file if it exists
    if os.path.exists("scan_output/templog.txt"):
        os.remove("scan_output/templog.txt")
    # now create it again as an empty file
    with open("scan_output/templog.txt", "w"):
        pass
    getImages(Queue(), 2, 0.25)
