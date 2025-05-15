from PyQt5 import QtCore, QtGui, QtWidgets, uic

from ros_map_editor.ui_map_editor import Ui_MapEditor

from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtCore import Qt

import math
import yaml
from PIL import Image
import sys
import os


class MapEditor(QtWidgets.QMainWindow):
    def __init__(self, fn):
        """Initialize the map editor with the given map file"""
        super(MapEditor, self).__init__()

        # two approaches to integrating tool generated ui file shown below
        
        # setup user interface directly from ui file
        #uic.loadUi('UI_MapEditor.ui', self)

        # setup user interface from py module converted from ui file
        self.ui = Ui_MapEditor()
        self.ui.setupUi(self)

        self.setMinimumSize(600, 600)

        self.ui.zoomBox.addItem("100 %", 1)
        self.ui.zoomBox.addItem("200 %", 2)
        self.ui.zoomBox.addItem("400 %", 4)
        self.ui.zoomBox.addItem("800 %", 8)
        self.ui.zoomBox.addItem("1600 %", 16)
        self.ui.zoomBox.currentIndexChanged.connect(self.handleZoom)

        self.ui.colorBox.addItem('alternate', 0)
        self.ui.colorBox.addItem('occupied', 1)
        self.ui.colorBox.addItem('unoccupied', 2)
        self.ui.colorBox.addItem('uncertain', 3)
        self.ui.colorBox.currentIndexChanged.connect(self.handleColor)
        self.color = 'alternate'

        self.box_selecting = False
        self.line_selecting = False
        self.box_select_mode = False
        self.line_select_mode = False
        self.start_pos = None
        self.end_pos = None

        self.read(fn)

        view_width = self.frameGeometry().width()

        self.min_multiplier = math.ceil(view_width / self.map_width_cells)
        self.zoom = 1
        self.pixels_per_cell = self.min_multiplier * self.zoom 

        self.draw_map()
        
        self.ui.boxSelectCheck.stateChanged.connect(self.toggleBoxSelect)
        self.ui.lineSelectCheck.stateChanged.connect(self.toggleLineSelect)

        self.ui.focusButton.clicked.connect(self.centerView)

        self.ui.closeButton.clicked.connect(self.closeEvent)
        self.ui.saveButton.clicked.connect(self.saveEvent)

        self.ui.graphicsView.horizontalScrollBar().valueChanged.connect(self.scrollChanged)
        self.ui.graphicsView.verticalScrollBar().valueChanged.connect(self.scrollChanged)

        self.ui.graphicsView.setMouseTracking(True)
        self.ui.graphicsView.viewport().installEventFilter(self)


    def eventFilter(self, source, event):
        """handle mouse interactions including box selection mode"""
        # mouse movement event handling
        if event.type() == QtCore.QEvent.MouseMove:
            pos = event.pos()
            x = pos.x() + self.ui.graphicsView.horizontalScrollBar().value()
            y = pos.y() + self.ui.graphicsView.verticalScrollBar().value()
            cell_x = math.floor(x / self.pixels_per_cell)
            cell_y = math.floor(y / self.pixels_per_cell)
            
            # line selection mode processing
            if self.ui.lineSelectCheck.isChecked() and event.buttons() == QtCore.Qt.LeftButton:
                if not self.line_selecting:
                    self.line_selecting = True
                    self.start_pos = (cell_x, cell_y)
                self.end_pos = (cell_x, cell_y)
                self.updateLinePreview()  # new method real time display of line preview
                return True
        
            # selection mode processing
            if self.ui.boxSelectCheck.isChecked() and event.buttons() == QtCore.Qt.LeftButton:
                if not self.box_selecting:
                    self.box_selecting = True
                    self.start_pos = (cell_x, cell_y)
                self.end_pos = (cell_x, cell_y)
                self.updateSelectionRect()  # update the selection display
                return True
                
            # normal mode processing
            elif event.buttons() == QtCore.Qt.LeftButton and self.color != 'alternate':
                self.fillCell(cell_x, cell_y)
                return True
        
        elif event.type() == QtCore.QEvent.MouseButtonRelease and self.line_selecting:
            self.line_selecting = False
            self.fillLineBetweenPoints()  # add method to fill cells on a straight line
            self.clearLinePreview()       # clear straight line preview
            return True
    
        # mouse release event handling
        elif event.type() == QtCore.QEvent.MouseButtonRelease and self.box_selecting:
            self.box_selecting = False
            self.fillSelectedArea()
            self.clearSelectionRect()
            return True
            
        return super().eventFilter(source, event)

    def paintEvent(self, e):
        """Handle paint events by updating the scroll position"""
        self.scrollChanged(0)


    def scrollChanged(self, val):
        """Update the minimap view when scrolling the main view"""
        
        if self.scene.width() and self.scene.height():
            x = int(self.ui.graphicsView.horizontalScrollBar().value() /  self.scene.width() * self.im.size[0])
            y = int(self.ui.graphicsView.verticalScrollBar().value() /  self.scene.height() * self.im.size[1])
            width = int(self.ui.graphicsView.viewport().size().width() /  self.scene.width() * self.im.size[0])
            height = int(self.ui.graphicsView.viewport().size().height() /  self.scene.height() * self.im.size[1])
            self.drawBox(x, y, width, height)


    def drawBox(self, x=5, y=5, width=50, height=50):
        """Draw a red rectangle on the minimap to show current view position"""
        im = self.im.convert("RGBA")
        data = im.tobytes("raw","RGBA")
        qim = QtGui.QImage(data, im.size[0], im.size[1], QtGui.QImage.Format_ARGB32)
        pix = QtGui.QPixmap.fromImage(qim)

        painter = QtGui.QPainter(pix)
        pen = QPen(Qt.red)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(x, y, width, height)

        painter.end()

        self.ui.label_2.setPixmap(pix)
        self.ui.label_2.show()

    def handleColor(self, index):
        """Set the current drawing color based on selection"""
        self.color = self.ui.colorBox.currentText()

    def handleZoom(self, index):
        """Update zoom level and redraw the map"""
        self.zoom = self.ui.zoomBox.currentData()
        self.pixels_per_cell = self.min_multiplier * self.zoom 
        self.draw_map()
        

    def read(self, fn):
        """Load and parse map file (.pgm) and its corresponding YAML configuration"""
        # try to open as fn or fn.pgm
        try:
            self.im = Image.open(fn)
            self.fn = fn
        except:
            fnpgm = fn + '.pgm'
            print(fnpgm)
            try:
                self.im = Image.open(fnpgm)
                self.fn = fnpgm
            except:
                #print(sys.exc_info()[0])
                print("ERROR:  Cannot open file", fn, "or", fnpgm)
                sys.exit(1)

        if self.im.format != 'PPM':
            print("ERROR:  This is not a PGM formatted file.")
            sys.exit(1)

        if self.im.mode != 'L':
            print("ERROR:  This PGM file is not of mode L.")
            sys.exit(1)   

        self.map_width_cells = self.im.size[0]
        self.map_height_cells = self.im.size[1]

        self.ui.filename_lbl.setText(self.fn) 
        self.ui.width_lbl.setText(str(self.map_width_cells))
        self.ui.height_lbl.setText(str(self.map_height_cells))

        fn_yaml = os.path.splitext(fn)[0] + '.yaml'
        try:
            stream = open(fn_yaml, "r")
            docs = yaml.load_all(stream, Loader=yaml.FullLoader)
            for doc in docs:
                self.occupied_thresh = doc['occupied_thresh']  # probability its occupied
                self.free_thresh = doc['free_thresh']  # probability its uncertain or occupied
                self.resolution = doc['resolution']    # in meters per cell
                self.origin_x = doc['origin'][0]
                self.origin_y = doc['origin'][1]
        except:
            print("ERROR:  Corresponding YAML file", fn_yaml, "is missing or incorrectly formatted.")
            sys.exit(1)


    def mapClick(self, event):
        """Handle mouse clicks on the map to change cell states"""
        # get current model value
        if self.box_select_mode or self.line_select_mode and event.button() == Qt.LeftButton:  # use the left mouse button in selection mode
           self.rect_selecting = True
        x = math.floor(event.scenePos().x() / self.pixels_per_cell)
        y = math.floor(event.scenePos().y() / self.pixels_per_cell)
        val = self.im.getpixel((x,y))

        if self.color == 'occupied':
            val = 0
        elif self.color == 'unoccupied':
            val = 255
        elif self.color == 'uncertain':
            val = 200
        else:
            # determine next value in sequence white->black->gray
            if val <= (255.0 * (1.0 - self.occupied_thresh)):  # if black, become gray
                val = 200
            elif val <= (255.0 * (1.0 - self.free_thresh)):  # else if gray, become white
                val = 255
            else:  # else its white, become black
                val = 0    

        # update model with new value
        self.im.putpixel((x,y), val)    

        # redraw cell in new color
        color = self.value2color(val)

        self.color_cell(x, y, color)


    def value2color(self, val):
        if val > (255.0 * (1.0 - self.free_thresh)):
            return Qt.white
        elif val > (255.0 * (1.0 - self.occupied_thresh)):
            return Qt.gray
        else:
            return Qt.black

    def color_cell(self, x, y, color):
        pen = QPen(color)
        pen.setWidth(1)
        if self.pixels_per_cell > 10:
            pen = QPen(Qt.lightGray)
        brush = QBrush(color)
        #x = x * self.pixels_per_cell
        #y = y * self.pixels_per_cell
  
        qrect = self.grids[x][y]
        qrect.setBrush(brush)
        qrect.setPen(pen)

        
    def add_cell(self, x, y, color):
        pen = QPen(color)
        pen.setWidth(1)
        if self.pixels_per_cell > 10:
            pen = QPen(Qt.lightGray)
        brush = QBrush(color)
        x = x * self.pixels_per_cell
        y = y * self.pixels_per_cell
        return self.scene.addRect(x, y, self.pixels_per_cell, self.pixels_per_cell, pen, brush)


    def draw_map(self):        
        self.scene = QtWidgets.QGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)
        self.scene.mousePressEvent = self.mapClick
        self.grids = []

        # draw the cells
        self.scene.clear()
        for x in range(0,self.map_width_cells):
            grid_col = []
            for y in range(0, self.map_height_cells):
                val = self.im.getpixel((x,y))
                color = self.value2color(val)
                qrect = self.add_cell(x,y,color)
                grid_col.append(qrect)
            self.grids.append(grid_col)

        # draw the grid lines
        if self.pixels_per_cell > 10:
            pen = QPen(Qt.lightGray)
            pen.setWidth(1)
            pixel_width = self.map_width_cells * self.pixels_per_cell
            pixel_height =self. map_height_cells * self.pixels_per_cell
            for x in range(0, pixel_width, self.pixels_per_cell):
                self.scene.addLine(x, 0, x, pixel_height, pen)
            for y in range(0, pixel_height, self.pixels_per_cell):
                self.scene.addLine(0, y, pixel_width, y, pen)

    def centerView(self):
        """center the main view to the thumbnail position"""
        if hasattr(self, 'im'):
            # calculate the center position
            center_x = self.im.size[0] // 2 
            center_y = self.im.size[1] // 2
            
            # convert to scene coordinates
            scene_x = center_x * self.scene.width() / self.im.size[0] - self.im.size[0]
            scene_y = center_y * self.scene.height() / self.im.size[1] - self.im.size[1]
            
            # adjust the scrollbar position
            self.ui.graphicsView.horizontalScrollBar().setValue(int(scene_x))
            self.ui.graphicsView.verticalScrollBar().setValue(int(scene_y))

    def auto_focus(self):
        # automatically calculate the best zoom ratio add at the end of the method
        viewport_width = self.ui.graphicsView.viewport().width()
        optimal_zoom = max(1, int(viewport_width / self.map_width_cells / self.min_multiplier))
        
        # set the closest available zoom level
        closest_index = 0
        min_diff = float('inf')
        for i in range(self.ui.zoomBox.count()):
            zoom = self.ui.zoomBox.itemData(i)
            if abs(zoom - optimal_zoom) < min_diff:
                min_diff = abs(zoom - optimal_zoom)
                closest_index = i
        
        self.ui.zoomBox.setCurrentIndex(closest_index)
        
        # auto center view
        self.centerView()
    
    def toggleBoxSelect(self, state):
        """switch to rectangle selection mode"""
        self.box_select_mode = (state == Qt.Checked)
        if self.box_select_mode and self.ui.lineSelectCheck.isChecked():
            self.ui.lineSelectCheck.setChecked(False)

    def updateSelectionRect(self):
        """update the selection rectangle display"""
        if hasattr(self, 'selection_rect'):
            self.scene.removeItem(self.selection_rect)
        
        min_x = min(self.start_pos[0], self.end_pos[0])
        max_x = max(self.start_pos[0], self.end_pos[0])
        min_y = min(self.start_pos[1], self.end_pos[1])
        max_y = max(self.start_pos[1], self.end_pos[1])
        
        rect = QtCore.QRectF(
            min_x * self.pixels_per_cell,
            min_y * self.pixels_per_cell,
            (max_x - min_x + 1) * self.pixels_per_cell,
            (max_y - min_y + 1) * self.pixels_per_cell
        )
        self.selection_rect = self.scene.addRect(rect, QPen(Qt.red, 2), QBrush(Qt.NoBrush))

    def fillSelectedArea(self):
        """fill all cells in the selected area"""
        color = self.ui.colorBox.currentText()
        min_x = min(self.start_pos[0], self.end_pos[0])
        max_x = max(self.start_pos[0], self.end_pos[0])
        min_y = min(self.start_pos[1], self.end_pos[1])
        max_y = max(self.start_pos[1], self.end_pos[1])
        
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if 0 <= x < self.map_width_cells and 0 <= y < self.map_height_cells:
                    self.fillCell(x, y)

    def clearSelectionRect(self):
        """clear selection display"""
        if hasattr(self, 'selection_rect'):
            self.scene.removeItem(self.selection_rect)
            del self.selection_rect


    def fillCell(self, x, y):
        """fill a single cell"""
        if self.color == 'occupied':
            val = 0
        elif self.color == 'unoccupied':
            val = 255
        elif self.color == 'uncertain':
            val = 200
        else:
            return
            
        self.im.putpixel((x, y), val)
        self.color_cell(x, y, self.value2color(val))

    def toggleLineSelect(self, state):
        """switch to straight line mode"""
        self.line_select_mode = (state == Qt.Checked)
        if self.line_select_mode and self.ui.boxSelectCheck.isChecked():
            self.ui.boxSelectCheck.setChecked(False)

    def updateLinePreview(self):
        """real time update linear preview"""
        if hasattr(self, 'line_preview'):
            self.scene.removeItem(self.line_preview)
        
        # use the bresenham algorithm to calculate a straight line path
        line_points = self.bresenham_line(self.start_pos[0], self.start_pos[1], 
                                        self.end_pos[0], self.end_pos[1])
        
        # create preview path dashed line
        path = QtGui.QPainterPath()
        path.moveTo(self.start_pos[0] * self.pixels_per_cell, 
                    self.start_pos[1] * self.pixels_per_cell)
        path.lineTo(self.end_pos[0] * self.pixels_per_cell, 
                self.end_pos[1] * self.pixels_per_cell)
        
        pen = QPen(Qt.blue, 1, Qt.DashLine)
        self.line_preview = self.scene.addPath(path, pen)

    def fillLineBetweenPoints(self):
        """fill in the straight path between two points"""
        points = self.bresenham_line(self.start_pos[0], self.start_pos[1],
                                    self.end_pos[0], self.end_pos[1])
        for x, y in points:
            if 0 <= x < self.map_width_cells and 0 <= y < self.map_height_cells:
                self.fillCell(x, y)

    def clearLinePreview(self):
        """clear straight line preview"""
        if hasattr(self, 'line_preview'):
            self.scene.removeItem(self.line_preview)
            del self.line_preview

    def bresenham_line(self, x0, y0, x1, y1):
        """bresenham line algorithm"""
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1
        
        if dx > dy:
            err = dx / 2.0
            while x != x1:
                points.append((x, y))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                points.append((x, y))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
                
        points.append((x, y))
        return points

    def closeEvent(self, event):
        self.close()

    def saveEvent(self, event):
        #self.im.save("map_old.pgm")
        self.im.save(self.fn)
        print('Saved', self.fn)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('ERROR:  Must provide map file name - with or without .pgm extension.')
        print()
        print('     $ python MapEditor.py map_file_name')
        print()
    app = QtWidgets.QApplication(sys.argv)
    window = MapEditor(sys.argv[1])
    window.show()
    sys.exit(app.exec_())