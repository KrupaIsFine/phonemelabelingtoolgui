import sys
import wave
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtCore import QRectF
import librosa
import librosa.display
from pyqtgraph import QtGui
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import QRectF
from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QApplication, QGraphicsPixmapItem
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSignal
from pyqtgraph import PlotWidget, ImageItem
from PyQt5.QtGui import QPixmap
import sounddevice as sd
from pyqtgraph import QtGui
from PyQt5.QtWidgets import QGraphicsProxyWidget
from pyqtgraph import GraphicsLayoutWidget
from pyqtgraph.graphicsItems.GraphicsLayout import GraphicsLayout
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSignal
from pyqtgraph import LinearRegionItem
import pyqtgraph as pg
from pycutie_3 import Ui_MainWindow # was using pycutie_3 previously, for working version
from scipy.signal import spectrogram
dct_obj = {}
prob_threshold = 0.5
color = QtGui.QColor(0, 0, 255, 3)  # Blue with 100 transparency
class Phonemes:
    def __init__(self, st, et, var, prob):
        self.st = st
        self.et = et
        self.var = var
        # self.fss = fss
        self.prob = prob


def create_cells(row):    
    new_cell = Phonemes(row[0], row[1], row[2], row[3])
        # Check if the syllable already exists in dct_obj
    if new_cell.var in dct_obj:
        # If the syllable exists, append the new cell's details to its existing entry
        dct_obj[new_cell.var].append((new_cell.st, new_cell.et, new_cell.prob))
    else:
        # If the syllable is enprobered for the first time, create a new list with its details
        dct_obj[new_cell.var] = [(new_cell.st, new_cell.et, new_cell.prob)]
    return new_cell

class LinearRegionItem(pg.LinearRegionItem):
    clicked = pyqtSignal(LinearRegionItem, float, float, int)
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
            print("Deselecting region")
            flag = 1
            self.clicked.emit(self, st, et, flag)
            # org_color = QColor('#0000ff')
            # org_color.setAlpha(50)
            # self.setBrush(org_color)
            # print("original color: ", self.brush.color().name())
            #self.setBrush(org_color)  
    
    def update_linedit(self, st, et, var, prob):
        self.ui.lineEdit.setText(st)
        self.ui.lineEdit_2.setText(et)
        self.ui.lineEdit_3.setText(var)
        # self.ui.lineEdit_4.setText(fss)
        self.ui.lineEdit_5.setText(prob)

    def highlight_region(self):
        # Toggle the appearance of the region item
        current_brush_color = self.brush.color().name()
        print("color: ", current_brush_color)       
        # Determine the new brush color
        new_brush_color = QColor('#0000ff')
        print("new color: ", new_brush_color.name())
        new_brush_color.setAlpha(25)       
        # Set the brush color
        self.setBrush(new_brush_color)
        print("Brush color after setting: ", self.brush.color().name())  # Debugging

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
        # Connect the Export As .lab button to the save_changes_lab method
        self.ui.pushButton_5.clicked.connect(self.save_changes_lab)
        # Connect the new region creation button press to a method
        self.ui.pushButton.clicked.connect(self.process_input_values)
        # Connect the Reset button to the reset method
        self.ui.pushButton_6.clicked.connect(self.reset)
        self.ui.pushButton_8.clicked.connect(self.play_audio)
        # Create a PyQtGraph PlotWidget
        # self.spectrogram_plot = pg.PlotWidget(background='w')
        # self.spectrogram_plot.setLabel("bottom", text="Time(s)")
        # self.spectrogram_plot.setLabel("left", text="Frequency (Hz)")
        # self.spectrogram_plot.setGeometry(0, 0, self.width(), 250)  # Adjust size and position as needed

        self.plot_item = pg.PlotItem() 
                # Set the range for the x-axis
        # self.plot_item.setXRange(0, 1)
        # Create a ViewBox
        self.viewbox = pg.ViewBox()
        self.viewbox2 = pg.ViewBox()
        # Set the range for the y-axis
        # self.plot_item.setYRange(0, 1)
        self.plot_item2 = pg.PlotItem() # Set a white background
        # self.plot_item.getPlotItem().setContentsMargins(0, 0, 0, 0)
        # Create a GraphicsLayoutWidget instance
        self.layout_widget = GraphicsLayoutWidget(show=True)
        # self.layout_widget.setBackground('w')  # Set background color to white

        # proxy = QGraphicsProxyWidget()
        # proxy.addItem(self.plot_item)
        # Set contents margins to zero
        
        p1 = self.layout_widget.addItem(self.plot_item, 0, 0, 1, 1)

       
        # Remove spacing between plots
        self.layout_widget.ci.layout.setRowSpacing(0, 0)
        self.layout_widget.setBackground('w')  # Set background color to white
        self.layout_widget.nextRow()
        
        # self.plot_item2 = pg.PlotItem(background='w')  # Set a white background
        # self.plot_item2.getPlotItem().setContentsMargins(0, 0, 0, 0)
        # proxy = QGraphicsProxyWidget()
        # proxy2 = QGraphicsProxyWidget()
        # proxy2.addItem(self.plot_item2)
        # Set contents margins to zero
        # self.viewbox.invertY(True)  # Set to True to invert the y-axis

        p2 = self.layout_widget.addItem(self.plot_item2, 1, 0, 1, 1)
        self.plot_item2.setYLink(self.plot_item)
        self.plot_item2.setXLink(self.plot_item)
        # Hide the x-axis ticks
        self.plot_item.getAxis("bottom").setTicks([])
        
        # Optionally, hide the x-axis label as well
        self.plot_item.getAxis("bottom").setLabel("")
        # self.plot_item.getAxis("left").setTicks([])
        
        # Optionally, hide the x-axis label as well
        self.plot_item.getAxis("left").setLabel("Amplitude")
        self.plot_item2.getAxis("left").setTicks([])
        
        # Optionally, hide the x-axis label as well
        self.plot_item2.getAxis("left").setLabel("Frequency")
        # Hide the axes of the second plot item
        # self.plot_item.getAxis('left').setVisible(False)
        # self.plot_item.getAxis('bottom').setVisible(False)
        # print("p1: ", len(p1))
        # print("p2: ", len(p2))
        if p1 is not None and p2 is not None:
            print("linking is working")
            p1.setYLink(p2)
        # Add the ViewBox to the layout

        # p2.setYLink('Plot1')  ## test linking by name
        scene = QGraphicsScene()
        # max_width = scene.sceneRect().width()
        # max_height = scene.sceneRect().height()
        # self.layout_widget.addItem(self.viewbox)
        self.layout_widget.setGeometry(0, 0, 1500, 800)
        # Scale the layout widget to ensure high-resolution rendering

        self.layout_widget.scale(16, 16)  # Increase scale factor as needed for higher resolution

        scene.addWidget(self.layout_widget)

        self.ui.graphicsView.setScene(scene)
        # self.layout_widget.addItem(self.plot_item)
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
        # Enable mouse interactions for zooming
        self.plot_item.setMouseEnabled(x=True, y=False)
        self.plot_item2.setMouseEnabled(x=True, y=False)
        # self.plot_item2.setMouseEnabled(x=True, y=False)
        # Add a vertical line at x=0
        self.zero_line = pg.InfiniteLine(pos=0, angle=0, movable=False, pen='k')  # Set pen color to black
        # self.top_line = pg.InfiniteLine(pos=1, angle=0, movable=False, pen='k')  # Set pen color to black
        # self.bottom_line = pg.InfiniteLine(pos=0.85, angle=0, movable=False, pen='k')  # Set pen color to black
        self.plot_item.addItem(self.zero_line)
        # self.plot_item.addItem(self.top_line)
        # self.plot_item.addItem(self.bottom_line)
        # Initialize dictionaries to store changed data
        self.changed_time = {}
        #self.changed_fss = {}

    def process_input_values(self):
        # Get text from the QLineEdit widgets
        start_time_text = self.ui.lineEdit_6.text()
        end_time_text = self.ui.lineEdit_3.text()
        syllable_text = self.ui.lineEdit_5.text()
        # fss_text = self.ui.lineEdit_4.text()
        prob_text = self.ui.lineEdit.text()
        # Perform further actions with the input values, e.g., display them, store them, etc.
        print("Start Time:", start_time_text)
        print("End Time:", end_time_text)
        print("syllable:", syllable_text)
        # print("fss:", fss_text)
        print("prob:", prob_text)
        # Convert text to appropriate data types (float or int)
        start_time = float(start_time_text)
        end_time = float(end_time_text)
        # fss = int(fss_text)
        prob = int(prob_text)
        # Call the method to create a new region item
        new_cell = start_time, end_time, syllable_text, prob
        create_cells(new_cell)  # Assuming create_cells accepts a Phonemes object as input
        self.create_region_item(start_time, end_time, syllable_text, prob)

    def load_audio_file(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Audio Files (*.wav *.mp3 *.ogg)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.plot_graph(self.layout_widget ,file_path)

    def load_csv_file(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Data Files (*.csv *.txt *.lab)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.plot_data(file_path)

    def save_changes_csv(self):
        # Create a list of dictionaries with the updated information
        final = []
        for var, details_list in dct_obj.items():
            for detail in details_list:
                final.append({'start_time': detail[0], 'end_time': detail[1], 'syllable': var, 'prob': detail[2]})
        print("final data: ", final)
        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(final)
        df.sort_values(by=['start_time'], inplace=True)
        df['start_time'] = df['start_time'].astype(int)
        df['end_time'] = df['end_time'].astype(int)
        print("dataframe: \n", df)
        # Save the DataFrame to a CSV file
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("CSV Files (*.csv)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            # float_formats = {'start_time': '%.5f', 'end_time': '%.5f'}
            df.to_csv(file_path, index=False)
            print(f"Changes saved to {file_path}")

    def save_changes_lab(self):
        # Create a list of dictionaries with the updated information
        final = []
        for var, details_list in dct_obj.items():
            for detail in details_list:
                final.append({'start_time': detail[0], 'end_time': detail[1], 'syllable': var, 'prob': detail[2]})
        print("final data: ", final)
        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(final)
        #print("lab dataframe before sort: \n", df)
        df['start_time'] = df['start_time'].astype(int)
        df['end_time'] = df['end_time'].astype(int)
        df.sort_values(by=['start_time'], inplace=True)
        #print("lab dataframe after sort: \n", df)
        # Save the DataFrame to a LAB file
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("LAB Files (*.lab)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            # float_formats = {'start_time': '%.5f'}
            df.to_csv(file_path, sep=' ', index=False, header=False)
            print(f"Changes saved to {file_path}")
            # Clear the dictionary after saving changes
            #dct_obj.clear()

    def connect_region_signals(self, region_item, text_item, var, prob):
        start_time, end_time = region_item.getRegion()
        print("region item: ", region_item.getRegion())
        print("st: ", start_time)
        print("et: ", end_time)
        print("region_item.sigRegionChanged.connect(lambda: self.handle_label_update(region_item, text_item, var, prob))")
        # Connect signals when the clickable_region_item's clicked signal is successfully connected
        region_item.sigRegionChanged.connect(lambda: self.handle_label_update(region_item, text_item, var, prob))
        print("region_item.sigRegionChanged.connect(lambda: self.update_changed_time(var, prob, region_item.getRegion()))")
        region_item.sigRegionChanged.connect(lambda: self.update_changed_time(var, prob, region_item.getRegion()))
        region_item.sigRegionChangeFinished.connect(lambda: self.adjust_next_region(region_item))

    def adjust_next_region(self, current_region_item):
        if current_region_item.movable:
            print("True")
            # Assuming region_items is a list containing all region items
            index_current = self.region_items.index(current_region_item)
            print("index current: ", index_current)
            print("len self region: ", len(self.region_items))
            #for end time boundary dragging
            if index_current < len(self.region_items) - 1:
                print("inside the newly added  block")
                next_region_item = self.region_items[index_current + 1]
                # Get the current region values
                current_start_time, current_end_time = current_region_item.getRegion()
                # Adjust the start time of the next region item (r2)
                next_region_item.setRegion([current_end_time, next_region_item.getRegion()[1]])
                previous_region_item = self.region_items[index_current - 1]
                previous_start_time, _ = previous_region_item.getRegion()
                previous_region_item.setRegion([previous_start_time, current_start_time])
                # Toggle the appearance of the region item
                # current_brush_color = self.brush.color().name()
                # print("color: ", current_brush_color)       
                # Determine the new brush color
                new_brush_color = QColor('#ffff00')
                # print("new color: ", new_brush_color.name())
                new_brush_color.setAlpha(25)       
                # Set the brush color
                next_region_item.setBrush(new_brush_color)
                current_region_item.setBrush(new_brush_color)
                # print("Brush color after setting: ", previous_region_item.brush.color().name())  # Debugging

    def display_clicked_values(self, region_item, start_time, end_time, flag):
        # Toggle the appearance of the region item
        color = QtGui.QColor(0, 0, 255, 25) 
        # current_brush_color = self.brush.color().name()
        # print("color: ", current_brush_color)       
        # Determine the new brush color
        new_brush_color = color
        print("new color: ", new_brush_color.name())       
        # Set the brush color
        # self.setBrush(new_brush_color)
        # print("Brush color after setting: ", self.brush.color().name())  # Debugging
        index_current = self.region_items.index(region_item)
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
        start_time, end_time = region_values
        print("changed time of new added var:\n start time ", start_time, "end time \n", end_time)
        if var in self.changed_time:
            self.changed_time[var].append((start_time, end_time, prob))
        else:    
            self.changed_time[var] = [(start_time, end_time, prob)]
        print("Updated dictionary details:", self.changed_time)
        # Update the corresponding values in dct_obj
        if var in dct_obj.items():
            dct_obj[var].append((start_time, end_time, prob))
        else:
        # If the syllable is enprobered for the first time, create a new list with its details
            dct_obj[var] = [(start_time, end_time, prob)]
        
        print("Updated dct_obj:", dct_obj)        

    def reset(self):
        # Clear all regions
        for region_item in self.region_items:
            self.plot_item.removeItem(region_item)
        print("region items to be cleared: \n", self.region_items)
        self.region_items = []
        # Clear all text items
        print("Text items to remove:", len(self.text_items))  # Debugging
        for text_item in self.text_items:
            self.plot_item.removeItem(text_item)
        self.text_items = []
        # Clear the waveform plot
        if self.curve is not None:
            self.plot_item.removeItem(self.curve)
            self.curve = None
        # Clear changed data dictionaries
        self.changed_time = {}
        self.plot_item.update()
        #self.changed_fss = {}

    def handle_label_update(self, region_item, text_item, var, prob):
        # Get the current values of the region
        region_values = region_item.getRegion()
        # Calculate the relative label position
        label_x, label_y = region_values # + (region_values[1] - region_values[0]) / 2
        print("region value[0]: ", label_x)
        # Update the text item text and position
        text_item.setText(f"{var}\n{prob}")
        # Set the text color
        text_item.setColor(pg.mkColor('blue'))
        text_item.setFont(pg.QtGui.QFont("Arial", 15))
        print("lable_x: ", label_x)
        print("lable_y: ", label_y)
        text_item.setPos(label_x, 35569)

        # region_item.setColor(pg.mkColor('red'))

    def plot_data(self, path):
        column_names = ['start_time', 'end_time', 'syllable', 'prob']
        file = pd.read_csv(path, header=None, sep=' ', names=column_names)
        # Set the first value of the 'start_time' column to 0
        # file['start_time'] = 0
        # print("start time = 0: \n", file['start_time'])
        # Shift the 'start_time' values up by one row
        # file['start_time'] = file['end_time'].shift(fill_value=0)
        # Convert 'start_time' and 'end_time' to float type
        # file['start_time'] = file['start_time'].astype(float)
        file['start_time'] = file['start_time'].astype(float)
        file['end_time'] = file['end_time'].astype(float)
        file['prob'] = file['prob'].astype(float).round(2)
        print("start time \t end time \n", file['start_time'], " \t", file['end_time'])
        print("pandas file after mod: \n", file)
        zipp = zip(file['start_time'], file['end_time'], file['syllable'], file['prob'])
        cells = [create_cells(row) for row in zipp]  
        index = 0
        avg_prob = file['prob'].mean()
        print("average prob: ", avg_prob)
        for cell in cells:
            if cell.prob > avg_prob:
                color = QtGui.QColor(0, 255, 0, 25)
                region_item = LinearRegionItem(values=(cell.st, cell.et,cell.var, cell.prob),orientation=pg.LinearRegionItem.Vertical, pen=pg.mkPen(color='k', width=1.5), movable=False, brush=pg.mkBrush(color), swapMode='block')
            else:
                color = QtGui.QColor(255, 0, 0, 25)
                region_item = LinearRegionItem(values=(cell.st, cell.et,cell.var, cell.prob),orientation=pg.LinearRegionItem.Vertical, pen=pg.mkPen(color='k', width=1.5), brush=pg.mkBrush(color), swapMode='block')
            self.region_items.append(region_item)
            print("appending to region_lst")
            self.region_lst.append([index, [cell.st, cell.et, cell.var, cell.prob]])
            # print("region item after appending: \n", self.region_lst)
            self.plot_item2.addItem(region_item)
            self.plot_item.addItem(region_item)
            # self.plot_item2.addItem(region_item)
            border_color = QtGui.QColor(255, 0, 0, 100)  # Red border
            # fill_color = QtGui.QColor(0, 255, 0, 100)  # Green fill with alpha value 100
            text_item = pg.TextItem(text=f"{cell.var}\n{cell.prob}", border=border_color, anchor=(0, 0))
            # Get the bounding rectangle of the region item
            # Get the bounding rectangle of the region item
            region_bounding_rect = region_item.boundingRect()

            # Set the position of the text item to match the position of the region item
            print("region_bounding_rect.x(), region_bounding_rect.y(): ", region_bounding_rect.x(), region_bounding_rect.y())
            text_item.setPos(region_bounding_rect.x(),region_bounding_rect.y() - text_item.boundingRect().height())

            # Add the text item to the plot widget
            self.plot_item.addItem(text_item)

            # Append the text item to the list of text items
            self.text_items.append(text_item)
            print("main region item:", region_item)
            index += 1
            # Connect the clicked signal of the region item to a slot
            region_item.clicked.connect(self.display_clicked_values)
            # Connect other signals and perform necessary setup
            self.connect_region_signals(region_item, text_item, cell.var, cell.prob)
            self.handle_label_update(region_item, text_item, cell.var, cell.prob)

        # self.plot_item.setLabel("bottom", text="Time")
        # self.plot_item.getPlotItem().getAxis("bottom").orientation = 'top'
        # self.plot_item.getAxis("bottom").setVisible(True)
        # self.plot_item.getAxis("left").setVisible(True)
        # self.plot_item.setYRange(cells[0].st, cells[-1].et)
        # self.plot_item2.setXRange(cells[0].st, cells[-1].et)
        # self.text_items = text_items
        # self.region_items = region_items
        print("region item before \n", self.region_items)
        #clickable_region_item = ClickableLinearRegionItem()
        print("region item after \n", self.region_items)
        # Connect the start_time_changed signal to a function or lambda expression

    def play_audio(self):
        start_time = self.start
        end_time = self.end
        # Set the flag to indicate that audio playback has started
        self.audio_playing = True
        print("Start Time:", start_time)
        print("End Time:", end_time)
        # Calculate start and end indices based on time
        start_index = int((start_time / 1e7) * self.sample_rate)
        end_index = int((end_time / 1e7) * self.sample_rate)
        print("start index:", start_index)
        print("end index:", end_index)
        # Extract audio data within the specified start and end time
        audio_segment = self.audio_data[start_index:end_index]
        print("audio segment: \n", audio_segment)
        # Increase buffer size to reduce underruns
        blocksize = 2048  # Experiment with different values to find the optimal buffer size
        print("Sample Rate:", self.sample_rate)
        # Start audio playback
        sd.play(audio_segment, samplerate=self.sample_rate, blocksize=blocksize)
        sd.wait()  # Wait until playback is finished
        # Set the flag to indicate that audio playback has finished
        self.audio_playing = False

    def create_region_item(self, start_time, end_time, syllable, prob):
        # Create the new region item
        if prob < 0.5:
            color = QtGui.QColor(255, 0, 0, 25)
        else:
            color = QtGui.QColor(0, 255, 0, 25)
        region_item = LinearRegionItem(values=(start_time, end_time, syllable, prob),
                                    orientation=pg.LinearRegionItem.Vertical,
                                    pen=pg.mkPen(color='k', width=1.5), brush=pg.mkBrush(color), swapMode='block')
        # Find the index where the new region item should be inserted
        insert_index = 0
        for index, region in enumerate(self.region_lst):
            if start_time < region[1][0]:  # Compare with start time of each existing region
                insert_index = index
                break
        else:
            insert_index = len(self.region_items)
        # Insert the new region item into the region_items list
        self.region_items.insert(insert_index, region_item)
        # print("insertes region item {0} at index {1}".format(region_item, insert_index))
        # Update the region list with the new region information
        self.region_lst.insert(insert_index, [insert_index, [start_time, end_time, syllable, prob]])
        # Add the region item to the plot widget
        self.plot_item.addItem(region_item)
        print(f"New region item created for syllable: {syllable}")
        # border_color = QtGui.QColor(255, 0, 0, 100)  # Red border
        # fill_color = QtGui.QColor(0, 255, 0, 100)  # Green fill with alpha value 100
        text_item = pg.TextItem(text=f"{syllable}\n{prob}", anchor=(0, 0))
        self.text_items.append(text_item)
        self.plot_item.addItem(text_item)
        print("Text items of new region: ", self.text_items)
        # Connect the clicked signal of the region item to a slot
        region_item.clicked.connect(self.display_clicked_values)
        self.connect_region_signals(region_item, text_item, syllable, prob)
        self.handle_label_update(region_item, text_item, syllable, prob)
        print(f"New region item created for syllable: {syllable}")
        # Clear QLineEdit boxes
        self.ui.lineEdit.clear()
        self.ui.lineEdit_6.clear()
        self.ui.lineEdit_3.clear()
        self.ui.lineEdit_4.clear()
        self.ui.lineEdit_5.clear()

    def plot_graph(self, layout_widget, path):
        # Open the audio file and extract data
        # layout = 
        # viewBox = pg.ViewBox()
        

        # Add plot_item2 to the layout
        # self.layout_widget.addItem(self.plot_item2, 1, 0, 1, 1)

        wave_obj = wave.open(path, 'rb')
        sample_width = wave_obj.getsampwidth()
        num_frames = wave_obj.getnframes()
        # Get the sample rate
        sample_rate = wave_obj.getframerate()
        audio_duration = num_frames / sample_rate
        self.sample_rate = sample_rate
        print("Sample rate: ", self.sample_rate)
        print("num_frames: ", num_frames)
        # Read the entire audio waveform
        audio_frames = wave_obj.readframes(num_frames)
        audio_data = np.frombuffer(audio_frames, dtype=np.int16) / float(2 ** (8 * sample_width - 1))
        #print("audio data \n", audio_data.tolist())
        self.audio_data = audio_data.tolist()
        # Plot the audio waveform horizontally
        # Plot the audio waveform horizontally
        time = np.linspace(0, audio_duration * 1e7, num_frames)
        #print("time data \n", time)
        amplitude = audio_data.tolist()
        self.audio_len = audio_duration
        print("Audio duration:", audio_duration, "seconds")
        # Create a curve on the first load
        if self.curve is None:
            self.curve = self.plot_item.plot(name="Audio Waveform", pen='r')
        # Update the curve with the initial audio data
        print("time: ", len(time))
        print("amplitude: ", len(amplitude))
        # self.curve.setData(time, amplitude)

        # Compute spectrogram
        n_fft = 2048  # FFT window size
        hop_length = 256  # Hop length (frame shift)
        D = librosa.stft(audio_data, n_fft=n_fft, hop_length=hop_length)
        spec = librosa.amplitude_to_db(np.abs(D), ref=np.max)
        # Transpose the spectrogram
        spec = spec.T
        # Rescale the spectrogram data to span from -1 to +1 range
        max_spec = np.max(spec)
        min_spec = np.min(spec)
        scaled_spec = ((spec - min_spec) / (max_spec - min_spec)) * 2 - 1
        # Adjust time axis
        time_resolution = hop_length / sample_rate
        time_axis = np.arange(0, audio_duration, time_resolution)

        # Plot spectrogram
        img = pg.ImageItem(scaled_spec)


        # Set the y-axis range of the spectrogram plot to span from -1 to +1
        self.plot_item2.setYRange(-1, 1)
        img.setRect(0, 0, audio_duration * 1e7, sample_rate / 2)
        # Set gray_r colormap
        cmap = pg.ColorMap([0, 255], [(255, 255, 255), (0, 0, 0)])
        lut = cmap.getLookupTable(0, 255, 256)
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
        self.plot_item2.getViewBox().setFixedWidth(1920 * 16)  # Adjust size as needed
        max_amplitude = max(max(amplitude), -min(amplitude))
        # Rescale each amplitude value individually to fit within the new y-axis range
        rescaled_amplitude = [(a / max_amplitude) * (sample_rate / 2) for a in amplitude]
        # Plot the rescaled waveform data
        self.curve.setData(time, rescaled_amplitude, pen='r')
        self.plot_item2.setXRange(0, audio_duration)
        self.plot_item2.setYRange(0, sample_rate / 2)

    def resizeEvent(self, event):
        # Resize the plot widget along with the central widget
        new_size = event.size()
        self.plot_item.setGeometry(0, 0, new_size.width(), 600)
        self.plot_item2.setGeometry(0, 0, new_size.width(), 600)
        event.accept()

def run_app():
    # Run the GUI tool
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()
