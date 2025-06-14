from setuptools import setup, find_packages

setup(
    name="ros_map_editor",
    version="0.1.1",
    description="A GUI editor for ROS map files in PGM format",
    long_description=open("README.md").read() if hasattr(__file__, "read") else "",
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