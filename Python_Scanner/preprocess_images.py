import os, cv2
from typing import Literal
from getImages import ScreenResolution


# given a path, preprocess the image for tesseract - for disk drive images
def preprocess_image(
    image_path,
    save_path=None,
    target_images_folder="../Target_Images",
):
    rarity_icon_threshold = 0.8
    agent_icon_threshold = 0.8
    # Load the image
    image = cv2.imread(image_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # non-adaptive thresholding
    threshold, binary_image = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Define icon paths for both resolutions
    rank_icons = {
        "S": ["zzz-disk-drive-S-icon.png", "zzz-disk-drive-S-icon-1080p.png"],
        "A": ["zzz-disk-drive-A-icon.png", "zzz-disk-drive-A-icon-1080p.png"],
        "B": ["zzz-disk-drive-B-icon.png", "zzz-disk-drive-B-icon-1080p.png"],
    }

    # Load and match all icon variants
    best_match = {"score": 0, "icon": None, "loc": None, "match_result": None}

    for rank, icon_files in rank_icons.items():
        for icon_file in icon_files:
            icon = cv2.imread(
                os.path.join(target_images_folder, icon_file),
                cv2.IMREAD_GRAYSCALE,
            )

            try:
                match_result = cv2.matchTemplate(
                    binary_image, icon, cv2.TM_CCOEFF_NORMED
                )
                max_val = cv2.minMaxLoc(match_result)[1]

                if max_val > rarity_icon_threshold and max_val > best_match["score"]:
                    best_match = {
                        "score": max_val,
                        "icon": icon,
                        "loc": cv2.minMaxLoc(match_result)[3],
                        "match_result": match_result,
                    }
            except cv2.error:
                continue

    rank_match = None
    # If we found a match above threshold, black out the icon area
    if best_match["icon"] is not None:
        binary_image[
            best_match["loc"][1] : best_match["loc"][1] + best_match["icon"].shape[0],
            best_match["loc"][0] : best_match["loc"][0] + best_match["icon"].shape[1],
        ] = 0
        rank_match = best_match[
            "match_result"
        ]  # Store the actual template matching result

    # remove agent icons
    # this should be done without recognition, as we don't know what the agent icons look like
    # the position of the agent icons can be done by enlarging the bounding box of the rarity icons
    # by a modifier, and then keeping the same y position but adjusting the x position so that the
    # edge of the bounding box hits the right side of the image

    agent_icon_size_modifier = 1.5
    agent_icon_y_offset = 0

    # calculate the agent icon bounding box
    if rank_match is not None:
        agent_icon_y = best_match["loc"][1] + agent_icon_y_offset
        agent_icon_width = int(best_match["icon"].shape[1] * agent_icon_size_modifier)
        agent_icon_height = int(best_match["icon"].shape[0] * agent_icon_size_modifier)

        # now push the agent icon bounding box to the right edge of the image
        agent_icon_x = binary_image.shape[1] - agent_icon_width

        # adjust the y offset so that the bounding box is centered on the same y position
        agent_icon_y = (
            agent_icon_y - (agent_icon_height - best_match["icon"].shape[0]) // 2
        )

        # set the agent icon bounding box to black
        binary_image[
            agent_icon_y : agent_icon_y + agent_icon_height,
            agent_icon_x : agent_icon_x + agent_icon_width,
        ] = 0

    # downscale the image so that it is 256 pixels wide, and keep the aspect ratio
    # we do this to keep the font size in the ideal range for tessaract (20px high capitals)
    # calculate the scaling factor
    desired_width = 384
    scaling_factor = desired_width / binary_image.shape[1]
    # calculate the new height
    desired_height = int(binary_image.shape[0] * scaling_factor)

    # resize the image
    binary_image = cv2.resize(
        binary_image, (desired_width, desired_height), interpolation=cv2.INTER_AREA
    )

    # Save the image if a save_path is provided
    if save_path:
        cv2.imwrite(save_path, binary_image)
        print(f"Preprocessed image saved to {save_path}")

    return binary_image


# given a path, preprocess the image for tesseract - for WEngine images
def preprocess_wengine_image(
    image_path,
    save_path=None,
    target_images_folder="./Target_Images",
    resize=True,
    resize_width=400,
):
    upgrade_rank = 1  # default to 1
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

    # black out the character / type section
    character_section_area = {
        "top": int(0.4 * image.shape[0]),
        "bottom": int(0.75 * image.shape[0]),
        "left": int(0.02 * image.shape[1]),
        "right": int(0.4 * image.shape[1]),
    }

    binary_image[
        character_section_area["top"] : character_section_area["bottom"],
        character_section_area["left"] : character_section_area["right"],
    ] = 0

    # black out the weapon section
    weapon_section_area = {
        "top": int(0.1 * image.shape[0]),
        "bottom": int(0.75 * image.shape[0]),
        "left": int(0.60 * image.shape[1]),
        "right": int(0.95 * image.shape[1]),
    }
    binary_image[
        weapon_section_area["top"] : weapon_section_area["bottom"],
        weapon_section_area["left"] : weapon_section_area["right"],
    ] = 0

    # black out the rarity section
    rarity_section_area = {
        "top": int(0.8 * image.shape[0]),
        "bottom": int(1 * image.shape[0]),
        "left": int(0.02 * image.shape[1]),
        "right": int(0.1 * image.shape[1]),
    }
    binary_image[
        rarity_section_area["top"] : rarity_section_area["bottom"],
        rarity_section_area["left"] : rarity_section_area["right"],
    ] = 0

    # downscale the image so that it is X pixels wide, and keep the aspect ratio
    # we do this to keep the font size in the ideal range for tessaract (20px high capitals)
    # calculate the scaling factor

    if resize:
        desired_width = resize_width
        scaling_factor = desired_width / binary_image.shape[1]
        desired_height = int(binary_image.shape[0] * scaling_factor)
        binary_image = cv2.resize(
            binary_image, (desired_width, desired_height), interpolation=cv2.INTER_AREA
        )

        # search for all instances of the upgrade star that indicates the upgrade level, note the number and black the space out
        upgrade_star_paths = [
            os.path.join(target_images_folder, "zzz-wengine-upgrade1.png"),  # 1
            os.path.join(target_images_folder, "zzz-wengine-upgrade2.png"),  # 2
            os.path.join(target_images_folder, "zzz-wengine-upgrade3.png"),  # 3
            os.path.join(target_images_folder, "zzz-wengine-upgrade4.png"),  # 4
            os.path.join(target_images_folder, "zzz-wengine-upgrade5.png"),  # 5
        ]

        # Try each upgrade template until we find a match
        upgrade_rank = 1  # default if no match found
        for rank, upgrade_path in enumerate(upgrade_star_paths, start=1):
            upgrade_template = cv2.imread(upgrade_path, cv2.IMREAD_GRAYSCALE)
            if upgrade_template is None:
                print(f"Warning: Could not load upgrade template {upgrade_path}")
                continue

            result = cv2.matchTemplate(
                binary_image, upgrade_template, cv2.TM_CCOEFF_NORMED
            )
            max_val = result.max()

            if max_val >= 0.9:  # If we found a good match
                upgrade_rank = rank
                h, w = upgrade_template.shape

                # Find the location of the match
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                top_left = max_loc

                # black out the matched area
                binary_image[
                    top_left[1] : top_left[1] + h,
                    top_left[0] : top_left[0] + w,
                ] = 0

                print(f"Found upgrade rank {upgrade_rank}")
                break  # Stop searching once we find a match

    # Save the image if a save_path is provided
    if save_path:
        cv2.imwrite(save_path, binary_image)
        print(f"Preprocessed image saved to {save_path}")

    return binary_image, upgrade_rank


### Character Preprocessing Functions ###
def preprocess_image_simple(image_path: str, save_path: str = None):
    """
    Preprocess the image by converting to grayscale and thresholding simply

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


def preprocess_skill_image(
    image_path: str, save_path: str = None, coreSkill: bool = False
):
    """
    Preprocess the skill image to get the skill level in white, and everything else in black

    Args:
        image_path (str): Path to the skill image
        save_path (str, optional): Path to save the preprocessed image
        coreSkill (bool, optional): Whether the skill is a core skill (so we can remove the play button)

    Returns:
        cv2.Mat: The preprocessed image
    """
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image at {image_path}")
        return None

    # black out the rightmost 30% of the image if it is a core skill
    if coreSkill:
        height, width = image.shape[:2]
        image[:, int(0.7 * width) :] = 0  # Set rightmost 30% to black
        blacked_out_image = image
    else:
        blacked_out_image = image

    # Convert the image to grayscale
    gray = cv2.cvtColor(blacked_out_image, cv2.COLOR_BGR2GRAY)

    # Aggressive threshold
    binary_image = cv2.threshold(
        gray,
        240,  # Fixed threshold value
        255,
        cv2.THRESH_BINARY,
    )[1]

    # save the image if a save_path is provided
    if save_path:
        cv2.imwrite(save_path, binary_image)
        print(f"Preprocessed image saved to {save_path}")

    return binary_image


def preprocess_character_weapon_image(
    resolution: ScreenResolution,
    image_path: str,
    save_path: str = None,
    target_folder: str = "./Target_Images",
    cutoff_offset: int = 10,
):
    """
    Preprocess the character weapon image to get a black and white image of just the weapon name (accounting for varying amount of lines of text and different resolutions)

    Args:
        resolution (ScreenResolution): Current screen resolution
        image_path (str): Path to the character weapon image
        save_path (str, optional): Path to save the preprocessed image
        target_folder (str, optional): Path to the target folder
        cutoff_offset (int, optional): Offset to add to the template match's y coordinate (percent of initial image height)

    Returns:
        cv2.Mat: The preprocessed image

    Used In:
        process_character_weapon_image()
    """

    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image at {image_path}")
        return None

    weapon_cutoff_image_suffix = (
        "-1440p" if resolution == ScreenResolution.RES_1440P else "-1080p"
    )
    weapon_cutoff_image_path = (
        f"{target_folder}/zzz-character-weapon-cutoff{weapon_cutoff_image_suffix}.png"
    )
    # load the template image
    template = cv2.imread(weapon_cutoff_image_path)
    if template is None:
        print(f"Error: Could not load template at {weapon_cutoff_image_path}")
        return None

    # perform template matching
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # cutoff the image vertically at the template match's y coordinate
    # only keep the portion above where the template was found, minus the offset percentage
    height, width = image.shape[:2]
    cutoff_y = max_loc[1] - int(
        cutoff_offset / 100 * height
    )  # Convert offset to percentage
    image = image[:cutoff_y, :]  # Keep only the top portion

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

### End of Character Preprocessing Functions ###

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # test the function
    image_path = "./scan_input/Partition1Scan7.png"
    save_path = "./scan_output/preprocessed_image_test.png"
    processed_image = preprocess_image(
        image_path, save_path=save_path, target_images_folder="./Target_Images"
    )
