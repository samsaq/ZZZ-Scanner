import os, cv2
from typing import Literal


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


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # test the function
    image_path = "./scan_input/Partition1Scan7.png"
    save_path = "./scan_output/preprocessed_image_test.png"
    processed_image = preprocess_image(
        image_path, save_path=save_path, target_images_folder="./Target_Images"
    )
