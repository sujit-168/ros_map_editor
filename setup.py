import os
import sys
from setuptools import setup, find_packages

# Constant known variables used throughout this file
cwd = os.path.dirname(os.path.abspath(__file__))

# Read in README.md for our long_description
with open(os.path.join(cwd, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

def get_packages_version():
    """Get the version of the packages"""
    with open(os.path.join(cwd, "ros_map_editor", "version.py")) as f:
        content = f.read()
        import re
        version = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
        if version:
            return version.group(1)
        raise RuntimeError("Unable to find __version__ string.")
    return version

# version
version = get_packages_version()
version_range_max = max(sys.version_info[1], 13) + 1

setup(
    name="ros_map_editor",
    version=version,
    description="A GUI editor for ROS map files in PGM format",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="sujit-168",
    author_email="sujie@tianbot.com",
    url="https://github.com/sujit-168/ros_map_editor/tree/main",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyQt5>=5.15.0",
        "Pillow>=8.0.0",
        "PyYAML>=5.1.0",
    ],
    entry_points={
        "console_scripts": [
            "ros_map_editor=ros_map_editor.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: User Interfaces",
    ],
    python_requires=">=3.6",
    keywords="ros, map, editor, pgm, robotics",
)