# a file to create synethic set name training data (line images and ground truths)
# these are for training tesseract to not memorize the set names
# I don't want to have to re-train the tesseract model every time a new set comes out
# accuracy of the text doesn't matter too much beyond the drive partition
# eg: of the example set name "Everflame Punk [5]" we need to make sure the [5] is accurate always
# the "Everflame Punk" can be corrected via cosine similarity later using valid_metadata.py

import os
import random
import string
from nltk.corpus import words
from PIL import Image, ImageDraw, ImageFont
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(
    ".."
)  # use sys.path to import the valid_metadata.py file (its in the parent directory)
from validMetadata import (
    valid_partition_1_main_stats,
    valid_partition_2_main_stats,
    valid_partition_3_main_stats,
    valid_partition_4_main_stats,
    valid_partition_5_main_stats,
    valid_partition_6_main_stats,
    valid_random_stats,
)

word_list = words.words()

# combine the valid main stats from valid_metadata.py into a single list and remove duplicates
valid_main_stats = list(
    set(
        valid_partition_1_main_stats
        + valid_partition_2_main_stats
        + valid_partition_3_main_stats
        + valid_partition_4_main_stats
        + valid_partition_5_main_stats
        + valid_partition_6_main_stats
    )
)


# generate a random set name (two words with a space in between followed by a space)
def generate_set_name():
    set_name = f"{random.choice(word_list)} {random.choice(word_list)}"
    # add a random parition to the set name (eg: [5]) - the number can randomly be between 1 and 6
    set_name += f" [{random.randint(1, 6)}]"
    return set_name


# generate a random percentage (between 0 and 100)
# percentages can have a decimal with one digit after it (eg: 50.5%)
# 50/50 chance of having a decimal
def generate_percentage():
    percentage = f"{random.randint(0, 100)}"
    if random.choice([True, False]):
        percentage += f".{random.randint(0, 9)}"
    percentage += "%"
    return percentage


# generate a random number in a given range
def generate_number(min=1, max=500):
    return f"{random.randint(min, max)}"


# generate a random main stat (picked at random from the valid main stats list)
def generate_main_stat():
    return random.choice(valid_main_stats)


# generate a random sub stat (picked at random from the valid random stats list)
def generate_sub_stat(ratio_with_upgrade=0.5):
    if random.random() < ratio_with_upgrade:
        return f"{random.choice(valid_random_stats)}+{generate_number(min=1, max=4)}"
    return random.choice(valid_random_stats)


# generate lvl string (eg: "Lv. 9/15"),
def generate_lvl_string(min_level=0, ranks=[("B", 9), ("A", 12), ("S", 15)]):
    # ranks are the possible types of lvl strings that can be generated (eg: a B rank has a max lvl of 9)
    rank, max_level = random.choice(ranks)
    return f"Lv. {random.randint(min_level, max_level)}/{max_level}"


# generate synethetic line image using a given set name
# the background is black and the text is white, using a font given by font_path
# the image should be size to fit the text with a little padding
def generate_line_image(gen_text, font_path, font_size=34, padding=8, padding_range=2):
    # randomize the padding a little bit to simulate real world boxing
    padding += random.randint(-padding_range, padding_range)

    # padding cannot be negative
    if padding < 0:
        padding = 0

    ZZZFont = ImageFont.truetype(font_path, font_size)
    # get the size of the text using getbbox
    left, top, right, bottom = ZZZFont.getbbox(gen_text)
    # calculate the width and height of the text
    width = right - left
    height = bottom - top

    # add padding to the width and height
    image_width = width + padding * 2
    image_height = height + padding * 2

    # create a blank image
    image = Image.new("RGB", (image_width, image_height), "black")
    draw = ImageDraw.Draw(image)

    # calculate the x and y positions of the text
    x = (image_width) // 2
    y = (image_height) // 2
    # draw the text on the image
    draw.text((x, y), gen_text, font=ZZZFont, fill="white", anchor="mm")
    return image


def generate_random_suffix(length=15):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def save_image_with_ground_truth(
    image, gen_string, image_dir, gt_dir, gen_function=generate_random_suffix
):
    # image name will be the set name with spaces replaced with underscores & the ground truth will be the set name
    image_name = gen_string.replace(" ", "_")

    # remove any non-alphanumeric characters from the image name since they cause issues saving the image
    image_name = "".join(e for e in image_name if e.isalnum())

    # check if the image.png and gt.txt already exist if so, add a random suffix to the image name
    while os.path.exists(f"{image_dir}/{image_name}.png") or os.path.exists(
        f"{gt_dir}/{image_name}.gt.txt"
    ):
        image_name += (
            gen_function()
        )  # there is a chance the same thing is generated again, but it's very low

    image.save(f"{image_dir}/{image_name}_synth.png")
    with open(f"{gt_dir}/{image_name}_synth.gt.txt", "w") as f:
        f.write(gen_string)


# function to generate x number of synthetic line images and ground truth pairs to the given output directories
def generate_synthetic_data(
    num_images, image_dir, gt_dir, font_path, gen_function=generate_set_name
):
    if num_images < 1:
        return
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    if not os.path.exists(gt_dir):
        os.makedirs(gt_dir)
    for i in range(num_images):
        gen_string = gen_function()
        image = generate_line_image(gen_string, font_path)
        save_image_with_ground_truth(image, gen_string, image_dir, gt_dir)
    print(f"Generated {num_images} synthetic images and ground truths")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    num_images = 10
    image_dir = "./training_data/synth_sub_images"
    gt_dir = "./training_data/synth_txt_truths"
    font_path = "./training_data/ZZZ-Font.ttf"
    gen_function = generate_sub_stat
    generate_synthetic_data(num_images, image_dir, gt_dir, font_path, gen_function)
