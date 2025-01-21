import os
import time
import re
import cv2
import pyautogui
import pytesseract
from keyboard import press
from validMetadata import character_names
from multiprocessing import Queue
from strsimpy import Cosine


class ScreenResolution:
    RES_1440P = (2560, 1440)
    RES_1080P = (1920, 1080)


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
    print("Switching to Zenless Zone Zero")
    ZZZWindow = pyautogui.getWindowsWithTitle("ZenlessZoneZero")[0]
    if ZZZWindow.isActive == False:
        pyautogui.press(
            "altleft"
        )  # Somehow this is needed to switch to the window, Why though?
        ZZZWindow.activate()
    print("Switched to Zenless Zone Zero")


def test_snapshot():
    screenshot = pyautogui.screenshot(
        "TestImages/test.png",
        region=(
            int(0.54 * screenWidth),
            int(0.255 * screenHeight),
            int(0.24 * screenWidth),
            int(0.08 * screenHeight),
        ),
    )
    screenshot.save("TestImages/test.png")


def navigate_character_details(target: str = "Base Stats"):
    """
    Navigate to a specific section of the character details page.

    Args:
        target (str): The section to navigate to.
                     Valid options: 'Base Stats', 'Skills', 'Equipment', 'Cinema'
    """
    if target not in ["Base Stats", "Skills", "Equipment", "Cinema"]:
        raise ValueError(
            "Invalid target. Must be one of: 'Base Stats', 'Skills', 'Equipment', 'Cinema'"
        )

    targetPos = None
    if target == "Base Stats":
        targetPos = (0.6 * screenWidth, 0.925 * screenHeight)
    elif target == "Skills":
        targetPos = (0.725 * screenWidth, 0.925 * screenHeight)
    elif target == "Equipment":
        targetPos = (0.87 * screenWidth, 0.925 * screenHeight)
    elif target == "Cinema":
        targetPos = (0.085 * screenWidth, 0.875 * screenHeight)

    pyautogui.moveTo(targetPos)
    pyautogui.click()


def is_character_owned(
    target_folder: str = "Target_Images",
    resolution: ScreenResolution = screenResolution,
    pageLoadTime: float = 0.25,
) -> bool:
    """
    Check if the current character is owned by looking for the preview mode popup.

    Args:
        target_folder (str): Folder containing the reference images
        resolution (ScreenResolution): Current screen resolution

    Returns:
        bool: True if character is owned, False if not owned

    Used In:
        get_character_snapshots()
    """
    wishReelPreviewPath = None
    if resolution == ScreenResolution.RES_1440P:
        wishReelPreviewPath = f"./{target_folder}/zzz-character-not-owned-1440p.png"
    elif resolution == ScreenResolution.RES_1080P:
        wishReelPreviewPath = f"./{target_folder}/zzz-character-not-owned-1080p.png"

    try:
        pyautogui.locateOnScreen(
            wishReelPreviewPath,
            confidence=0.9,
            region=(
                int(0.25 * screenWidth),
                int(0.4 * screenHeight),
                int(0.5 * screenWidth),
                int(0.2 * screenHeight),
            ),
        )
        # If we get here, the image was found (character is not owned)
        press("esc")
        print("Agent is not owned")
        return False
    except pyautogui.ImageNotFoundException:
        # Image not found means the agent is owned
        press("esc")
        print("Agent is owned")
        return True
    except Exception as e:
        # Handle any other unexpected errors
        print(f"Error checking if agent is owned: {e}")
        return False


# function to get the various screenshots for a character for later processing
def get_character_snapshots(
    agent_num: int,
    queue: Queue = None,
    target_folder: str = "Target_Images",
    output_folder: str = "scan_input",
    resolution: ScreenResolution = screenResolution,
    pageLoadTime: float = 0.25,
):
    wishReelIconPosition = (0.92 * screenWidth, 0.2 * screenHeight)
    pyautogui.moveTo(wishReelIconPosition)
    pyautogui.click()
    pyautogui.sleep(pageLoadTime)

    if not is_character_owned(target_folder, resolution, pageLoadTime):
        return

    # take a snapshot of the character name
    screenshot = pyautogui.screenshot(
        region=(
            int(0.54 * screenWidth),
            int(0.255 * screenHeight),
            int(0.24 * screenWidth),
            int(0.08 * screenHeight),
        ),
    )
    screenshot.save(f"./{output_folder}/agent_{agent_num}_name.png")
    if queue:
        queue.put(f"./{output_folder}/agent_{agent_num}_name.png")

    # character level and maxlevel snapshot
    screenshot = pyautogui.screenshot(
        region=(
            int(0.54 * screenWidth),
            int(0.4 * screenHeight),
            int(0.1325 * screenWidth),
            int(0.08 * screenHeight),
        ),
    )
    screenshot.save(f"./{output_folder}/agent_{agent_num}_level.png")


# intended to be a main function of sorts to be called in getImages.py for character image collection
def get_characters():
    num_characters = len(character_names)
    characters_in_final_row = 7
    startPosition = (0.57 * screenWidth, 0.045 * screenHeight)
    distance_between_characters = 0.0525 * screenWidth
    pyautogui.moveTo(startPosition)

    # click through all the scrollable characters
    for i in range(num_characters - characters_in_final_row):
        pyautogui.click()
        get_character_snapshots()
        pyautogui.moveTo(startPosition)  # move back after character scan
        pyautogui.scroll(-1)

    # click through the final row
    cur_character_position = startPosition
    for i in range(characters_in_final_row):
        pyautogui.click()
        pyautogui.sleep(0.5)
        get_character_snapshots()
        # move to the next character, using absolute coordinates since we move the mouse in get_character_snapshots()
        cur_character_position = (
            cur_character_position[0] + distance_between_characters,
            cur_character_position[1],
        )
        # if at the end of the row, don't move the mouse since there are no more characters
        if i != characters_in_final_row - 1:
            pyautogui.moveTo(cur_character_position)


### Character Scanner Functions ###


def scan_image(image_path):
    # default_config = "--oem 1 -l eng"
    # old_config = "--oem 1 -l ZZZ --tessdata-dir ./tessdata"
    config = "--oem 1 -l eng --psm 6"  # force NN+LSTM finetuned model
    try:
        text = pytesseract.image_to_string(image_path, config=config)
    except Exception as e:
        print("Error while scanning image: " + str(e))
        return None
    split_text = text.split("\n")
    split_text = list(filter(None, split_text))
    return split_text


def find_closest_stat(
    stat, valid_stats
):  # find the closest stat in the input list to the input stat
    cosine = Cosine(2)
    closest_stat = None
    closest_stat_similarity = 0
    for valid_stat in valid_stats:
        similarity = cosine.similarity(stat, valid_stat)
        if similarity >= closest_stat_similarity:
            closest_stat_similarity = similarity
            closest_stat = valid_stat

    # if the closest and original stat are different, log it, use string comparison to check since similarity would also catch substat upgrades
    if closest_stat != stat:
        print(f"Corrected {stat} to {closest_stat}")

    return closest_stat


def find_closest_number(value: str, valid_numbers: list[str]) -> str:
    """
    Find the closest number from a list of valid numbers

    Args:
        value (str): The number to check (as string)
        valid_numbers (list[str]): List of valid numbers (as strings)

    Returns:
        str: The closest valid number (as string)
    """
    try:
        num = int(value)
        valid_nums = [int(x) for x in valid_numbers]
        closest = min(valid_nums, key=lambda x: abs(x - num))

        if closest != num:
            print(f"Corrected {value} to {closest}")

        return str(closest)
    except ValueError:
        print(f"Error converting '{value}' to number, returning last valid number")
        return valid_numbers[-1]


def preprocess_name_image(image_path: str, save_path: str = None):
    """
    Preprocess the name image to get the agent name

    Args:
        image_path (str): Path to the name image
        save_path (str, optional): Path to save the preprocessed image

    Returns:
        cv2.Mat: The preprocessed image

    Used In:
        process_name_image()
    """
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image at {image_path}")
        return None

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Aggressive threshold
    binary_image = cv2.threshold(
        gray,
        240,  # Fixed threshold value
        255,
        cv2.THRESH_BINARY,
    )[1]

    # NOTE: We aren't resizing the image here like in the other preprocess_images.py functions
    # This is because the font size already varies between characters, and I don't want to have to set a resize width per character

    # Save the image if a save_path is provided
    if save_path:
        cv2.imwrite(save_path, binary_image)
        print(f"Preprocessed image saved to {save_path}")

    return binary_image


def preprocess_level_image(image_path: str, save_path: str = None):
    """
    Preprocess the level image to get the agent level

    Args:
        image_path (str): Path to the level image
        save_path (str, optional): Path to save the preprocessed image

    Returns:
        cv2.Mat: The preprocessed image

    Used In:
        process_level_image()
    """
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image at {image_path}")
        return None

    # part of the level text we later want to extract is black, so we need to grab the subsection
    height, width = image.shape[:2]
    subsection_height = int(0.6 * height)  # 0.8 - 0.2 = 0.6
    subsection_width = int(0.325 * width)  # 1 - 0.675 = 0.325
    y_start = int(0.2 * height)
    x_start = int(0.675 * width)

    level_text_subsection = image[
        y_start : y_start + subsection_height,
        x_start : x_start + subsection_width,
    ]

    # white any black pixels in the subsection
    level_text_subsection[level_text_subsection == 0] = 255

    # resize the subsection to half size since the font size of the max level is larger
    new_height = subsection_height // 2
    new_width = subsection_width // 2
    resized_subsection = cv2.resize(level_text_subsection, (new_width, new_height))

    # calculate centering offsets
    y_offset = (subsection_height - new_height) // 2
    x_offset = (subsection_width - new_width) // 2

    # black out the original subsection area
    image[
        y_start : y_start + subsection_height,
        x_start : x_start + subsection_width,
    ] = 0

    # paste the resized subsection in the center of the blacked out area
    image[
        y_start + y_offset : y_start + y_offset + new_height,
        x_start + x_offset : x_start + x_offset + new_width,
    ] = resized_subsection

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Aggressive threshold
    binary_image = cv2.threshold(
        gray,
        240,  # Fixed threshold value
        255,
        cv2.THRESH_BINARY,
    )[1]

    # NOTE: We aren't resizing the image here like in the other preprocess_images.py functions
    # This is because the font size already varies between characters, and I don't want to have to set a resize width per character

    # Save the image if a save_path is provided
    if save_path:
        cv2.imwrite(save_path, binary_image)
        print(f"Preprocessed image saved to {save_path}")

    return binary_image


def process_name_image(image_path: str) -> str:
    """
    Process the name image to get the agent name

    Args:
        image_path (str): Path to the name image

    Returns:
        str: The agent name, corrected to the known list of agent names
    """
    processed_image = preprocess_name_image(image_path)
    # concatenate the text from the image
    text = scan_image(processed_image)
    text = " ".join(text)
    # correct it to the known list of agent names
    text = find_closest_stat(text, character_names)
    return text


def process_level_image(image_path: str) -> tuple[str, str]:
    """
    Process the level image to get the agent level

    Args:
        image_path (str): Path to the level image

    Returns:
        str: The agent level
    """
    processed_image = preprocess_level_image(image_path)
    text = scan_image(processed_image)

    # if the text is only one string, we need to split it and grab the two level numbers from it
    if len(text) == 1:
        # Match two sequences of two digits
        match = re.search(r"(\d{2}).*?(\d{2})", text[0])
        if match:
            current_level = match.group(1)
            max_level = match.group(2)
        else:
            print(f"Could not parse levels from text: {text[0]}")
            print("Assuming max leveled character (60/60)")
            current_level = "60"
            max_level = "60"
    else:
        # if not, we can clean and grab the two numbers from the list
        # clean all members of non-digit characters
        text = [re.sub(r"\D", "", t) for t in text]
        # strip all of them
        text = [t.strip() for t in text]
        # remove any empty strings
        text = list(filter(None, text))
        current_level = text[0]
        max_level = text[1]

    # correction for the level text
    # the maxlevel is one of "10", "20", "30", "40", "50", "60"
    # the cur level must be equal to or less than the max level (up to 10 below)

    # correct the max level to the nearest valid level
    max_level = find_closest_number(max_level, ["10", "20", "30", "40", "50", "60"])

    # correct the current level
    # make sure the current level is less than or equal to the max level
    if int(current_level) > int(max_level):
        current_level = max_level

    # if it is more than 10 below the max level, set it to ten below the max level
    if int(current_level) < int(max_level) - 10:
        current_level = int(max_level) - 10

    return current_level, max_level


### End of Character Scanner Functions ###

if __name__ == "__main__":
    # set cwd to the script location
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    switchToZZZ()
    # time.sleep(0.25)
    # get_characters()
    # test_snapshot()
    # get_character_snapshots()

    # targetImage = "TestImages/testLvlImg.png"
    # get a subsection of the image
    # image = cv2.imread(targetImage)
    # if image is None:
    #     print(f"Error: Could not load image at {targetImage}")
    #     exit(1)

    # height, width = image.shape[:2]  # Correct order: height, width
    # level_text_subsection = image[
    #     int(0.2 * height) : int(0.8 * height),
    #     int(0.675 * width) : int(1 * width),
    # ]
    # cv2.imwrite("TestImages/testLvlImgSubsection.png", level_text_subsection)
    # image = preprocess_level_image(targetImage)
    # cv2.imwrite("TestImages/testLvlImgPreprocessed.png", image)
    # text = scan_image("TestImages/testLvlImgPreprocessed.png")
    # print(text)

    # level_image_path = "TestImages/testLvlImg.png"
    # current_level, max_level = process_level_image(level_image_path)
    # print(f"Current Level: {current_level}, Max Level: {max_level}")

    navigate_character_details("Cinema")
