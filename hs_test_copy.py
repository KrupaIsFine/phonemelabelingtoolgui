import sys
import wave
import csv
import numpy as np
import pandas as pd
import librosa
import sounddevice as sd
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QGraphicsScene, QGraphicsSceneContextMenuEvent, QMenu, QPushButton
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap, QPainter,QColor, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from pyqtgraph import LinearRegionItem, GraphicsLayoutWidget
from pycutie_3 import Ui_MainWindow # Working version of UI File

DEBUG = False
dct_obj = {}
color = QtGui.QColor(0, 0, 255, 3)  # Blue with 100 transparency
class Phonemes:
    def __init__(self, st, et, var, prob):
        self.st = st
        self.et = et
        self.var = var
        self.prob = prob

def create_cells(row):  
    if DEBUG:
        print("row: ", row)
        print("row0: ", row[0])
        print("row1: ", row[1])
    new_cell = Phonemes(row[0], row[1], row[2], row[3])
    return new_cell

def create_dct_obj(lst):
    for item in lst:
        index = item[0]
        st = item[1][0]
        et = item[1][1]
        var = item[1][2]
        prob = item[1][3]
        if DEBUG:
            print("index = item[0] st = item[1][0]et = item[1][1]var = item[1][2]prob = item[1][3]: ", index,
            st,
            et,
            var,
            prob)
        dct_obj[index] = [(st, et, var, prob)]


class LinearRegionItem(pg.LinearRegionItem):
    clicked = pyqtSignal(LinearRegionItem, float, float, int)
    # brush_color = None
    # Custom signal with region values
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, ev):
        super().mouseDoubleClickEvent(ev)
        flag = 0
        region_values = self.getRegion()
        st = region_values[0]
        et = region_values[1]

        if ev.button() == Qt.LeftButton:
            # Emit the highlighted signal with the region values
            self.highlight_region()
            # self.update_linedit()
            self.clicked.emit(self, st, et, flag)
        else:
            if DEBUG:
                print("Deselecting region")
            flag = 1
            self.clicked.emit(self, st, et, flag)



    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        flag = 0
        region_values = self.getRegion()
        st = region_values[0]
        et = region_values[1]
        menu = QMenu()
        action1 = menu.addAction("Select")
        action2 = menu.addAction("Deselect")
        # Drag yes
        # Drag no
        # action3 = menu.addAction("Play")
        
        action = menu.exec_(event.screenPos())
        if action == action1:
            if DEBUG:
                print("Action 1 triggered")
            self.highlight_region()
            self.clicked.emit(self, st, et, flag)
        elif action == action2:
            self.deselect_region()
            flag = 1
            self.clicked.emit(self, st, et, flag)
            if DEBUG:
                print("Action 2 triggered")
        # elif action == action3:
        #     ui = MyMainWindow()
        #     ui.play_audio(self)
        #     flag = 1
        #     self.clicked.emit(self, st, et, flag)
        #     if DEBUG:
        #         print("Action 3 triggered")


    def highlight_region(self):
        # Toggle the appearance of the region item
        current_brush_color = self.brush.color()
        self.brush_color = current_brush_color
        # Determine the new brush color
        new_brush_color = QColor('#0000ff')
        new_brush_color.setAlpha(25)       
        # Set the brush color
        self.setBrush(new_brush_color)
        self.setMovable(True)
        if DEBUG:
            print("color: ", current_brush_color.name())       
            print("new color: ", new_brush_color.name())
            print("Brush color after setting: ", self.brush.color().name())  # Debugging

    def deselect_region(self):
        color = QtGui.QColor(0, 0, 255, 45)
        self.setBrush(color)
        if DEBUG:
            print("Brush color after deselecting-if statement: ", self.brush.color().name())  # Debugging



class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Connect the Load Audio button to the load_audio_file method
        self.ui.pushButton_2.clicked.connect(self.load_audio_file)
        # Connect the Load CSV button to the load_audio_file method
        self.ui.pushButton_3.clicked.connect(self.load_csv_file)
        # Connect the Export As .csv button to the save_changes_csv method
        self.ui.pushButton_12.clicked.connect(self.save_changes_csv)
        self.ui.pushButton_11.clicked.connect(self.zoom_in)
        self.ui.pushButton_10.clicked.connect(self.zoom_out)
        self.ui.pushButton_4.clicked.connect(self.process_input_values)
        self.zoom_factor = 1.0
        # Connect the Export As .lab button to the save_changes_lab method
        self.ui.pushButton_5.clicked.connect(self.save_changes_lab)
        # Connect the new region creation button press to a method
        self.ui.pushButton.clicked.connect(self.process_input_values)
        # Connect the Reset button to the reset method
        self.ui.pushButton_6.clicked.connect(self.reset)
        self.ui.pushButton_8.clicked.connect(self.play_audio)
        self.threshold = 0
        self.path = None

        self.viewbox = pg.ViewBox()
        self.viewbox2 = pg.ViewBox()
        self.plot_item = pg.PlotItem() 

        self.plot_item2 = pg.PlotItem() # Set a white background

        # Create a GraphicsLayoutWidget instance
        self.layout_widget = GraphicsLayoutWidget(show=True)

        self.region_items2 = []

        # Set contents margins to zero
        # Set border around the layout widget
        self.layout_widget.setStyleSheet("border: 1px solid black;")
        p1 = self.layout_widget.addItem(self.plot_item)
       
        # Remove spacing between plots
        self.layout_widget.ci.layout.setRowSpacing(0, 0)
        self.layout_widget.setBackground('w')  # Set background color to white
        self.layout_widget.nextRow()
        p2 = self.layout_widget.addItem(self.plot_item2)
        if p1 is not None and p2 is not None:
            if DEBUG:
                print("linking is working")
            p2.setYLink(p1)
        scene = QGraphicsScene()
        # Set the size policy for the layout widget to expand and fill the available space
        self.layout_widget.setSizePolicy(
            pg.QtWidgets.QSizePolicy.Expanding,
            pg.QtWidgets.QSizePolicy.Expanding
        )
        self.layout_widget.setGeometry(0, 0, 1700, 770)
        # Scale the layout widget to ensure high-resolution rendering
        scene.addWidget(self.layout_widget)
        scene.setSceneRect(scene.itemsBoundingRect())
        self.ui.graphicsView.setScene(scene)

        self.start = 0
        self.end = 0
        self.sample_rate = 0
        self.audio_data = []

        # Initialize curve
        self.curve = None
        self.region_items = []
        self.text_items = []
        self.audio_len = 0
        self.region_lst = []
        self.avg_prob = 0
        self.reg_ref = None
        # Enable mouse interactions for zooming
        self.plot_item.setMouseEnabled(x=True, y=False)
        self.plot_item2.setMouseEnabled(x=True, y=False)
        # Add a vertical line at x=0
        self.zero_line = pg.InfiniteLine(pos=0, angle=0, movable=False, pen='k')  # Set pen color to black
        self.plot_item.addItem(self.zero_line)
        # Initialize dictionaries to store changed data
        self.changed_time = {}
        # Connect the sceneRectChanged signal of the scene to adjust the layout widget's size
        scene.sceneRectChanged.connect(self.adjustLayoutWidgetSize)

    def zoom_in(self):
        # Increase zoom factor
        self.plot_item.getViewBox().scaleBy((0.5, 0.5))
        # print("Zoom In:", self.zoom_factor)

    def zoom_out(self):
        # Decrease zoom factor
        self.plot_item.getViewBox().scaleBy((2, 2))
        # print("Zoom Out:", self.zoom_factor)

    def update_linedit(self, region_item, var, prob):
            print("region item: ", region_item)

            st, et = region_item.getRegion()
            var = var
            prob = prob
            print("st = region_item[0] et = region_item[1] phone = region_item[2] prob = region_item[3]", st, et, var, prob)
            self.ui.lineEdit_6.setText(str(st))
            self.ui.lineEdit_3.setText(str(et))
            self.ui.lineEdit_5.setText(str(var))
            self.ui.lineEdit_4.setText(str(prob))

    def update(self, reg_ref, st, et, var, prob):
        r = reg_ref
        s = st
        e = et
        v = var
        p = prob
        self.adjust_next_region(r, s, e, v, p, flag=1)
        # self.handle_label_update(r, s, e, v, p)

            

    def adjustLayoutWidgetSize(self, rect):
        # Resize the plot widget along with the central widget
        self.plot_item.setGeometry(rect.toRect())
        self.plot_item2.setGeometry(rect.toRect())
        # Adjust the size of the layout widget to fit the scene's bounding rect
        self.layout_widget.setGeometry(rect.toRect())
        self.setGeometry(rect.toRect())

    def process_input_values(self, region_item):
        # Get text from the QLineEdit widgets
        print("linear region item: ", region_item)
        if region_item != False:
            self.reg_ref = region_item 
        else:
            region_item = self.reg_ref
        print("self.reg_ref: ", self.reg_ref)
        start_time_text = self.ui.lineEdit_6.text()
        end_time_text = self.ui.lineEdit_3.text()
        syllable_text = self.ui.lineEdit_5.text()
        # fss_text = self.ui.lineEdit_4.text()
        prob_text = float(self.ui.lineEdit_4.text())
        # Perform further actions with the input values, e.g., display them, store them, etc.
        print("syllable:", syllable_text)
        print("prob:", prob_text)
        if DEBUG:
            print("Start Time:", start_time_text)
            print("End Time:", end_time_text)
            print("syllable:", syllable_text)
            print("prob:", prob_text)
        # Convert text to appropriate data types (float or int)
        start_time = int(float(start_time_text))
        end_time = int(float(end_time_text))
        prob = float(prob_text)
        # Call the method to create a new region item
        sender_button = self.sender()
        if isinstance(sender_button, QPushButton):
            if sender_button == self.ui.pushButton:
                # Perform actions for pushButton_1 click
                print("Button 1 clicked")
                self.create_region_item(start_time, end_time, syllable_text, prob)
            elif sender_button == self.ui.pushButton_4:
                # Perform actions for pushButton_2 click
                print("Button 2 clicked")
                self.update(self.reg_ref, start_time, end_time, syllable_text, prob)
        

    def load_audio_file(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Audio Files (*.wav *.mp3 *.ogg)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.plot_graph(file_path)

    def load_csv_file(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Data Files (*.csv *.txt *.lab)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.plot_data(file_path)

    def save_changes_csv(self):
        # Create a list of dictionaries with the updated information
        final = []
        for index, details_list in dct_obj.items():
            for detail in details_list:
                final.append({'start_time': detail[0], 'end_time': detail[1], 'syllable': detail[2], 'prob': float(detail[3])})
        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(final)
        df['start_time'] = df['start_time'].astype(int)
        df['end_time'] = df['end_time'].astype(int)
        # df['prob'] = df['prob'].map(lambda x: '%.6f' % x)
        df.sort_values(by=['start_time'], inplace=True)
        if DEBUG:
            print("dataframe: \n", df)
        # Save the DataFrame to a CSV file
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("CSV Files (*.csv)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            # Use below line if you want to export with decimal values, change the datatype to float above too
            # float_formats = {'prob': '%.6f'}
            df.to_csv(file_path, index=False)
            if DEBUG:
                print(f"Changes saved to {file_path}")

    def save_changes_lab(self):
        # Create a list of dictionaries with the updated information
        final = []
        for index, details_list in dct_obj.items():
            if DEBUG:
                print("details list: ", index, details_list)
            for values in details_list:   
                final.append({'end_time': values[1], 'syllable': values[2], 'prob': float(values[3])})
                # else:
            #     print(f"Ignoring invalid detail: {detail}")
        if DEBUG:
            print("final data: ", final)
            print("length of final: ", len(final))
        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(final)
        #print("lab dataframe before sort: \n", df)
        # df['end_time'] = df['end_time'].astype(int)
        # df['start_time'] = df['start_time'].astype(int)
        df['end_time'] = df['end_time'].astype(int)
        df['prob'] = df['prob'].map(lambda x: '%.6f' % x)
        df.sort_values(by=['end_time'], inplace=True)
        #print("lab dataframe after sort: \n", df)
        # Save the DataFrame to a LAB file
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("LAB Files (*.lab)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            # Use below line if you want to export with decimal values, change the datatype to float above too
            # float_formats = {'prob': '%.6f'}
            df.to_csv(file_path, sep=' ', index=False, header=False)
            if DEBUG:
                print(f"Changes saved to {file_path}")
            # Clear the dictionary after saving changes
            #dct_obj.clear()

    def connect_region_signals(self, region_item, region_item2, text_item, var, prob):
        start_time, end_time = region_item.getRegion()
        if DEBUG:
            print("region item: ", region_item.getRegion())
            print("st: ", start_time)
            print("et: ", end_time)
            print("var: ", var)
            print("prob: ", prob)
            print("region_item.sigRegionChanged.connect(lambda: self.handle_label_update(region_item, text_item, var, prob))")
        # Connect signals when the clickable_region_item's clicked signal is successfully connected
        region_item.sigRegionChanged.connect(lambda: self.sync_region_items(region_item, region_item2))
        if DEBUG:
            print("region_item.sigRegionChanged.connect(lambda: self.update_changed_time(var, prob, region_item.getRegion()))")
        

        region_item.clicked.connect(lambda: self.update_linedit(region_item, var, prob))
        # print("text item: ", text_item)
        region_item.clicked.connect(lambda: self.process_input_values(region_item))
        region_item.sigRegionChanged.connect(lambda: self.handle_label_update(region_item, text_item, var, prob))
        # region_item.sigRegionChanged.connect(lambda: self.update_linedit(region_item))
        region_item.sigRegionChanged.connect(lambda: self.update_changed_time(var, prob, region_item))
        print("Region item before adjust: ", region_item)
        region_item.sigRegionChangeFinished.connect(lambda: self.adjust_next_region(region_item, start_time, end_time, var, prob, flag=0))     

    def adjust_next_region(self, current_region_item, st, et, var, prob, flag):
        # flag = flag
        s = st
        e = et
        v = var
        p = prob
        flag = flag
        print("current_region_item: ", current_region_item)
        # print("s,e,v,p,flag: ", s, e, v, p, flag)
        if current_region_item.movable:
            if DEBUG:
                print("True")
            index_current = self.region_items.index(current_region_item)
            print("index current: ", index_current)
            if DEBUG:
                print("index current: ", index_current)
                print("len self region: ", len(self.region_items))
            #for end time boundary dragging
            if index_current < len(self.region_items) - 1:
                if DEBUG:
                    print("inside the newly added  block")
                next_region_item = self.region_items[index_current + 1]
                # Get the current region values
                if flag == 0 :
                    current_start_time, current_end_time = current_region_item.getRegion()
                else:
                    current_start_time = s
                    current_end_time = e
                    var = v
                    prob = p
                # Adjust the start time of the next region item (r2)
                next_region_item.setRegion([current_end_time, next_region_item.getRegion()[1]])
                previous_region_item = self.region_items[index_current - 1]
                print("previous region items: ", previous_region_item)
                previous_start_time, _ = previous_region_item.getRegion()
                # previous_start_time = int(previous_start_time)
                # current_start_time = int(current_start_time)
                previous_region_item.setRegion([previous_start_time, current_start_time])      
                # Determine the new brush color
                new_brush_color = QColor('#ffff00')
                # print("new color: ", new_brush_color.name())
                new_brush_color.setAlpha(25)       
                # Set the brush color
                current_region_item.setBrush(new_brush_color)
                # print("Brush color after setting: ", previous_region_item.brush.color().name())  # Debugging

    def display_clicked_values(self, region_item, start_time, end_time, flag):
        # Toggle the appearance of the region item
        color = QtGui.QColor(0, 0, 255, 25)        
        # Determine the new brush color
        new_brush_color = color
        if DEBUG:
            print("new color: ", new_brush_color.name())       
        index_current = self.region_items.index(region_item)
        if DEBUG:
            print("Index of clicked region item: ", index_current)
            print("Region clicked with start time:", start_time, "and end time:", end_time)
            print("flag: ", flag)
        if flag == 0:
            self.start = start_time
            self.end = end_time
        else:
            self.start = 0
            self.end = self.audio_len
            return

    def update_changed_time(self, var, prob, region_values):

        start_time, end_time = region_values.getRegion()
        index_current = self.region_items.index(region_values)
        if DEBUG:
            print("index_current: ", index_current)
            print("changed time of new added var:\n start time ", start_time, "end time \n", end_time)
        start_time = float(int(start_time))
        end_time = float(int(end_time))
        # Update self.changed_time
        self.changed_time[index_current] = [start_time, end_time, var, prob]

        # Update dct_obj
        dct_obj[index_current] = [(start_time, end_time, var, prob)]
        # print("Updated dct_obj:", dct_obj)


    def reset(self):
        # Clear all regions
        for region_item in self.region_items:
            self.plot_item.removeItem(region_item)
        self.region_items = []
        # Clear all text items
        if DEBUG:
            print("region items to be cleared: \n", self.region_items)
            print("Text items to remove:", len(self.text_items))  # Debugging
        for text_item in self.text_items:
            self.plot_item.removeItem(text_item)
        self.text_items = []
        # Clear the waveform plot
        if self.curve is not None:
            self.plot_item.removeItem(self.curve)
            self.curve = None
        self.plot_item2.clear()
        # Clear changed data dictionaries
        self.changed_time = {}
        self.plot_item.update()


    def handle_label_update(self, region_item, text_item, var, prob):
        # Get the current values of the region
        region_values = region_item.getRegion()
        # Calculate the relative label position
        label_x, label_y = region_values # + (region_values[1] - region_values[0]) / 2
        # Update the text item text and position
        text_item.setText(f"{var}\n{round(prob, 1)}")
        # Set the text color
        text_item.setColor(pg.mkColor('blue'))
        text_item.setFont(QtGui.QFont("Arial", 20))
        if DEBUG:
            print("region value[0]: ", label_x)
            print("lable_x: ", label_x)
            print("lable_y: ", label_y)
        text_item.setPos(label_x, 35000)

    def sync_region_items(self, source_region_item, target_region_item):
        # Synchronize region boundaries
        st, et = source_region_item.getRegion()
        if DEBUG:
            print("before syncing")
        target_region_item.setBrush(pg.mkColor(0, 0, 0, 0))    
        target_region_item.setRegion([st, et])
        if DEBUG:
            print("after syncing")

    def plot_data(self, path):
        column_names = ['end_time', 'prob', 'syllable']
        file = pd.read_csv(path, skiprows=1, header=None, sep=' ', names=column_names)
        file['start_time'] = file['end_time'].shift(fill_value=0)
        file['end_time'] = file['end_time'].astype(float)
        file['prob'] = file['prob'].astype(float)
        if DEBUG:
            print("start time \t end time \n", file['start_time'], " \t", file['end_time'])
            print("pandas file after mod: \n", file)
        zipp = zip(file['start_time'], file['end_time'], file['syllable'], file['prob'])
        cells = [create_cells(row) for row in zipp]  
        index = 0
        avg_prob = file['prob'].mean()
        if DEBUG:
            print("average prob: ", avg_prob)
        color = QtGui.QColor(0, 0, 255, 45)
        for cell in cells:
            region_item = LinearRegionItem(values=(cell.st, cell.et,cell.var, cell.prob),orientation=pg.LinearRegionItem.Vertical, pen=pg.mkPen(color='k', width=1.5), brush=pg.mkBrush(color), swapMode='block')
            region_item2 = LinearRegionItem(values=(cell.st, cell.et,cell.var, cell.prob),orientation=pg.LinearRegionItem.Vertical, pen=pg.mkPen(color='k', width=1.5), movable=False, brush=pg.mkColor(0, 0, 0, 0), swapMode='block')            
            # region_item.addAction(self.newAction)
            self.region_items.append(region_item)
            self.region_lst.append([index, [cell.st, cell.et, cell.var, cell.prob]])
            # print("region item after appending: \n", self.region_lst)
            index += 1
            self.plot_item.addItem(region_item)
            self.plot_item2.addItem(region_item2)
            # self.plot_item2.addItem(region_item)
            border_color = QtGui.QColor(255, 0, 0, 100)  # Red border
            fill_color = QtGui.QColor(240, 240, 240, 255)  # Green fill with alpha value 100
            text_item = pg.TextItem(text=f"{cell.var}\n{cell.prob}", border=border_color, fill=fill_color)
            # Get the bounding rectangle of the region item
            region_bounding_rect = region_item.boundingRect()
            # Set the position of the text item to match the position of the region item
            text_item.setPos(region_bounding_rect.x(),region_bounding_rect.y() - text_item.boundingRect().height())
            # Add the text item to the plot widget
            self.plot_item.addItem(text_item)
            # Append the text item to the list of text items
            self.text_items.append(text_item)
            create_dct_obj(self.region_lst)
            # Connect the clicked signal of the region item to a slot
            region_item.clicked.connect(self.display_clicked_values)
            # Connect sigRegionChanged signals of both region items
            # Connect other signals and perform necessary setup
            self.connect_region_signals(region_item, region_item2, text_item, cell.var, cell.prob)
            self.handle_label_update(region_item, text_item, cell.var, cell.prob)


    def play_audio(self):
        start_time = self.start
        end_time = self.end
        # Set the flag to indicate that audio playback has started
        self.audio_playing = True
        if DEBUG:
            print("Start Time:", start_time)
            print("End Time:", end_time)
            print("Start Time:", start_time)
            print("End Time:", end_time)
        start = start_time
        end = end_time
        if DEBUG:
            print("start: ", start)
            print("end: ", end)
        # Calculate start and end indices based on time
        start_index = int((start_time) * self.sample_rate)
        end_index = int((end_time) * self.sample_rate)
        if DEBUG:
            print("start index:", start_index)
            print("end index:", end_index)
        # Extract audio data within the specified start and end time
        audio_segment = self.audio_data[start_index:end_index]
        # Increase buffer size to reduce underruns
        blocksize = 2048  # Experiment with different values to find the optimal buffer size
        if DEBUG:
            print("Sample Rate:", self.sample_rate)
        # Start audio playback
        sd.play(audio_segment, samplerate=self.sample_rate, blocksize=blocksize)
        sd.wait()  # Wait until playback is finished
        # Set the flag to indicate that audio playback has finished
        self.audio_playing = False

    def create_region_item(self, start_time, end_time, var, prob):
        st = start_time
        et = end_time
        v = var
        p = prob
        if DEBUG:
            print("starttime: ", st)
            print("endtime: ", et)
            print("var: ", v)
            print("prob: ", p)
        # Find the index where the new region item should be inserted
        insert_index = 0
        temp_region = []
        for index, region in enumerate(self.region_lst):
            if DEBUG:
                print("index, region: ", index, region)
            if start_time < region[1][0]:  # Compare with start time of each existing region
                insert_index = index
                temp_region.extend(region)
                if DEBUG:
                    print("temp_region: ", temp_region)
                break
        else:
            insert_index = len(self.region_items)

        for region in reversed(self.region_lst[insert_index:]):
            index = region[0]
            if DEBUG:
                print("index: ", index)
                print("region: ", region)
            region[0] += 1
            # print("index: ", index)
            if DEBUG:
                print("region: ", region)
        self.region_lst.insert(insert_index, [insert_index, [float(st), float(et), v, p]])

        dct_obj.clear()
        # region_dct = {}
        sum = 0
        count = 0
        
        # print("insert_index: ", insert_index)
        for region in self.region_lst:
            index = region[0]
            st = region[1][0]
            et = region[1][1]
            var = region[1][2]
            prob = region[1][3]
            sum += prob
            count += 1

        avg_prob = sum / count
        self.avg_prob = avg_prob

        self.reset()
        self.ui.lineEdit.clear()
        self.ui.lineEdit_6.clear()
        self.ui.lineEdit_3.clear()
        self.ui.lineEdit_4.clear()
        self.ui.lineEdit_5.clear()
        self.plot_graph(path=self.path)
        # self.new_plot()


    def plot_graph(self, path):
        # Open the audio file and extract data
        if self.path is None:
            self.path = path

        # Add plot_item2 to the layout
        wave_obj = wave.open(path, 'rb')
        sample_width = wave_obj.getsampwidth()
        num_frames = wave_obj.getnframes()
        # Get the sample rate
        sample_rate = wave_obj.getframerate()
        audio_duration = num_frames / sample_rate
        self.sample_rate = sample_rate
        if DEBUG:
            print("Sample rate: ", self.sample_rate)
            print("num_frames: ", num_frames)
        # Read the entire audio waveform
        audio_frames = wave_obj.readframes(num_frames)
        audio_data = np.frombuffer(audio_frames, dtype=np.int16) / float(2 ** (8 * sample_width - 1))
        if DEBUG:
            print("audio data \n", audio_data.tolist())
        self.audio_data = audio_data.tolist()
        # Plot the audio waveform horizontally
        time = np.linspace(0, audio_duration, num_frames)
        #print("time data \n", time)
        amplitude = audio_data.tolist()
        self.audio_len = audio_duration
        if DEBUG:
            print("Audio duration:", audio_duration, "seconds")
        # Create a curve on the first load
        if self.curve is None:
            self.curve = self.plot_item.plot(name="Audio Waveform", pen='r')
        # Update the curve with the initial audio data
        if DEBUG:
            print("time: ", len(time))
            print("amplitude: ", len(amplitude))
            print("amplitude: \n", amplitude)
        
        # Path to the output file
        file_path = "/home/krupa/Documents/Krupavathy/amplitude_data.csv"
        with open(file_path, mode='w', newline='') as file:
            for item in amplitude:
                file.write(str(item) + '\n')
        # Compute spectrogram
        # Correctly plotting the spectrogram without much pixelation
        n_fft = 1024 # FFT window size crct - 64
        hop_length = 512 # Hop length (frame shift) crct - 16
        D = librosa.stft(audio_data, n_fft=n_fft, hop_length=hop_length)
        # # Magnitude Details
        spec = librosa.amplitude_to_db(np.abs(D), ref=np.max)
        file_path = "/home/krupa/Documents/Krupavathy/spectrogram_data.csv"
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(spec)
        if DEBUG:
            print("spectrogram: \n", spec)
            print("spectrogram before: ", len(spec))
        # Transpose the spectrogram
        spec = spec.T
        if DEBUG:
            print("spectrogram: ", len(spec))
        # Adjust time axis
        # Plot spectrogram
        img = pg.ImageItem(spec)
        # Set the y-axis range of the spectrogram plot to span from -1 to +1
        img.setRect(0, 0, audio_duration, sample_rate / 2)
        # Generate a lookup table (lut) using Viridis colormap
        # Create inverted grayscale colormap
        gray_values = np.linspace(255, 0, 256)
        cmap = pg.ColorMap([0, 1], [(0, 0, 0), (255, 255, 255)])  # Start and end colors are black and white
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        lut[:, 0:3] = np.vstack((gray_values, gray_values, gray_values)).T

        # Set the lookup table for the image
        img.setLookupTable(lut)
        # Convert the image to a QPixmap and then to a QImage with the desired resolution
        image_width = 1920 * 4
        image_height = 1080 * 4
        pixmap = QPixmap(image_width, image_height)
        pixmap.fill(Qt.transparent)  # Fill with a transparent background
        painter = QPainter(pixmap)
        img.paint(painter, QRectF(0, 0, image_width, image_height))
        painter.end()
        qimage = pixmap.toImage()
        # Convert QImage to NumPy array
        qimage = qimage.rgbSwapped()  # Convert to RGB format
        image_array = np.array(qimage.bits().asarray(qimage.width() * qimage.height() * 4)).reshape((qimage.height(), qimage.width(), 4))
        # Transpose the image array to display vertically
        image_array = np.transpose(image_array, (1, 0, 2))
        # Set the image data for the ImageItem
        img.setImage(image_array)
        # Add the ImageItem to the plot
        self.plot_item2.addItem(img)
        # Increase the size of the plot_item2's viewport
        max_amplitude = max(max(amplitude), -min(amplitude))
        # Rescale each amplitude value individually to fit within the new y-axis range
        rescaled_amplitude = [(a / max_amplitude) * (sample_rate / 2) for a in amplitude]
        # Plot the rescaled waveform data
        self.curve.setData(time, rescaled_amplitude, pen='r')
        # Hide the x-axis ticks
        self.plot_item.getAxis("bottom").setTicks([])     
        # Optionally, hide the x-axis label as well
        self.plot_item.getAxis("bottom").setLabel("")
        # Optionally, hide the x-axis label as well
        self.plot_item.getAxis("left").setLabel("Amplitude")
        # Optionally, hide the x-axis label as well
        self.plot_item2.getAxis("left").setLabel("Frequency")
        self.plot_item2.getAxis("bottom").setLabel("Time")
        self.plot_item.getAxis('left').setWidth(int(75))
        self.plot_item2.getAxis('left').setWidth(int(75))
        self.plot_item2.setXRange(0, audio_duration)
        self.plot_item2.setYRange(0, (sample_rate / 2) - 12000)
        # self.plot_item2.setYLink(self.plot_item)
        self.plot_item2.setXLink(self.plot_item)

    def resizeEvent(self, event):
        # Resize the plot widget along with the central widget
        new_size = event.size()
        self.plot_item.setGeometry(0, 0, new_size.width(), 400)
        self.plot_item2.setGeometry(0, 0, new_size.width(), 400)
        event.accept()

def run_app():
    # Run the GUI tool
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()