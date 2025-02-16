# ZZZ-Scanner

A program that scans your drive discs in [Zenless Zone Zero](https://zenless.hoyoverse.com/) & saves them for use in the [Zenless Optimizer](https://github.com/samsaq/ZZZ-Drive-Disk-Optimizer)

## How to use

Download the latest portable zip or installer from the releases page and use the .exe from there as admin. You might need to alter the page load speed (time to wait for the equipment screen to load) or disk scan speed (time to wait in between taking snapshots of disks so that the game can load the next one) if your computer is a little slow.

Once you click the start scan button **DON'T TOUCH ANYTHING** until the scanner finishes moving - it'll break the scan otherwise and you'll need to restart. Once it does, alt tab back to the scanner & the file explorer window opened with the scan_data.json file you'll upload to the [Zenless Optimizer](https://github.com/samsaq/ZZZ-Drive-Disk-Optimizer) to analyze.

## Compatibility

The scanner is just for PC, and works on **1080p and 1440p screens**. If you want support for another resolution, you can send me a few UI images snipped from ZZZ at fullscreen at that resolution (see the Python Scanner's Target Images folder) for me to use, or get them and edit the getImages.py file to use the new resolution's images (as is already done for 1080p and 1440p) and submit a PR.
