#!/usr/bin/env python3
"""
Main entry point for the ROS Map Editor application.
"""

import sys
import argparse
from ros_map_editor.map_editor import MapEditor
from PyQt5 import QtWidgets


def main():
    """
    Main function that parses command line arguments and starts the application.
    """
    print("Starting ROS Map Editor...")
    parser = argparse.ArgumentParser(description='ROS Map Editor - A GUI tool for editing ROS map files')
    parser.add_argument('map_file', help='Path to the map file (.pgm or without extension)')
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.0')
    
    args = parser.parse_args()
    print(f"Opening map file: {args.map_file}")
    
    app = QtWidgets.QApplication(sys.argv)
    try:
        window = MapEditor(args.map_file)
        window.show()
        print("Map editor window displayed")
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error starting map editor: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()