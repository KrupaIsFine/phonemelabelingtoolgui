import sys
import wave
import numpy as np
import pandas as pd
import sounddevice as sd
from pyqtgraph import QtGui
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSignal
from pyqtgraph import LinearRegionItem
import pyqtgraph as pg
from pycutie_3 import Ui_MainWindow

dct_obj = {}
color = QtGui.QColor(0, 0, 255, 3)  # Blue with 100 transparency
class Phonemes:
    def __init__(self, st, et, var, prob, count):
        self.st = st
        self.et = et
        self.var = var
        self.prob = prob
        self.count = count


def create_cells(row):    
    new_cell = Phonemes(row[0], row[1], row[2], row[3], row[4])
        # Check if the variable already exists in dct_obj
    if new_cell.var in dct_obj:
        # If the variable exists, append the new cell's details to its existing entry
        dct_obj[new_cell.var].append((new_cell.st, new_cell.et, new_cell.prob, new_cell.count))
    else:
        # If the variable is encountered for the first time, create a new list with its details
        dct_obj[new_cell.var] = [(new_cell.st, new_cell.et, new_cell.prob, new_cell.count)]
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
            org_color = QColor('#0000ff')
            org_color.setAlpha(50)
            self.setBrush(org_color)
            print("original color: ", self.brush.color().name())
            #self.setBrush(org_color)  
    
    def update_linedit(self, st, et, var, prob, count):
        self.ui.lineEdit.setText(st)
        self.ui.lineEdit_2.setText(et)
        self.ui.lineEdit_3.setText(var)
        self.ui.lineEdit_4.setText(prob)
        self.ui.lineEdit_5.setText(count)

    def highlight_region(self):
        # Toggle the appearance of the region item
        current_brush_color = self.brush.color().name()
        print("color: ", current_brush_color)       
        # Determine the new brush color
        new_brush_color = QColor('#ffff00')
        print("new color: ", new_brush_color.name())
        new_brush_color.setAlpha(20)       
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
        self.plot_widget = pg.PlotWidget(background='w')  # Set a white background
        # Set contents margins to zero
        self.plot_widget.getPlotItem().setContentsMargins(0, 0, 0, 0)
        scene = QGraphicsScene()
        scene.addWidget(self.plot_widget)
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
        # Enable mouse interactions for zooming
        self.plot_widget.setMouseEnabled(x=True, y=False)
        # Add a vertical line at x=0
        self.zero_line = pg.InfiniteLine(pos=0, angle=0, movable=False, pen='k')  # Set pen color to black
        self.plot_widget.addItem(self.zero_line)
        # Initialize dictionaries to store changed data
        self.changed_time = {}
        #self.changed_probability = {}

    def process_input_values(self):
        # Get text from the QLineEdit widgets
        start_time_text = self.ui.lineEdit_6.text()
        end_time_text = self.ui.lineEdit_3.text()
        variable_text = self.ui.lineEdit_5.text()
        probability_text = self.ui.lineEdit_4.text()
        count_text = self.ui.lineEdit.text()
        # Perform further actions with the input values, e.g., display them, store them, etc.
        print("Start Time:", start_time_text)
        print("End Time:", end_time_text)
        print("Variable:", variable_text)
        print("Probability:", probability_text)
        print("Count:", count_text)
        # Convert text to appropriate data types (float or int)
        start_time = float(start_time_text)
        end_time = float(end_time_text)
        probability = int(probability_text)
        count = int(count_text)
        # Call the method to create a new region item
        new_cell = start_time, end_time, variable_text, probability, count
        create_cells(new_cell)  # Assuming create_cells accepts a Phonemes object as input
        self.create_region_item(start_time, end_time, variable_text, probability, count)

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
        for var, details_list in dct_obj.items():
            for detail in details_list:
                final.append({'start_time': detail[0], 'end_time': detail[1], 'variable': var, 'probability': detail[2], 'count': detail[3]})
        print("final data: ", final)
        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(final)
        df.sort_values(by=['start_time'], inplace=True)
        df['start_time'] = df['start_time'].map('{:,.5f}'.format)
        df['end_time'] = df['end_time'].map('{:,.5f}'.format)
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
                final.append({'end_time': detail[1], 'probability': detail[2], 'variable': var, 'count': detail[3]})
        print("final data: ", final)
        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(final)
        #print("lab dataframe before sort: \n", df)
        df.sort_values(by=['end_time'], inplace=True)
        df['end_time'] = df['end_time'].map('{:,.5f}'.format)
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

    def connect_region_signals(self, region_item, text_item, var, prob, count):
        start_time, end_time = region_item.getRegion()
        print("region item: ", region_item.getRegion())
        print("st: ", start_time)
        print("et: ", end_time)
        print("region_item.sigRegionChanged.connect(lambda: self.handle_label_update(region_item, text_item, var, prob, count))")
        # Connect signals when the clickable_region_item's clicked signal is successfully connected
        region_item.sigRegionChanged.connect(lambda: self.handle_label_update(region_item, text_item, var, prob, count))
        print("region_item.sigRegionChanged.connect(lambda: self.update_changed_time(var, prob, count, region_item.getRegion()))")
        region_item.sigRegionChanged.connect(lambda: self.update_changed_time(var, prob, count, region_item.getRegion()))
        region_item.sigRegionChangeFinished.connect(lambda: self.adjust_next_region(region_item))

    def adjust_next_region(self, current_region_item):
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

    def display_clicked_values(self, region_item, start_time, end_time, flag):
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

    def update_changed_time(self, var, prob, count, region_values):
        start_time, end_time = region_values
        print("changed time of new added var:\n start time ", start_time, "end time \n", end_time)
        if var in self.changed_time:
            self.changed_time[var].append((start_time, end_time, prob, count))
        else:    
            self.changed_time[var] = [(start_time, end_time, prob, count)]
        print("Updated dictionary details:", self.changed_time)
        # Update the corresponding values in dct_obj
        if var in dct_obj.items():
            dct_obj[var].append((start_time, end_time, prob, count))
        else:
        # If the variable is encountered for the first time, create a new list with its details
            dct_obj[var] = [(start_time, end_time, prob, count)]
        
        print("Updated dct_obj:", dct_obj)        

    def reset(self):
        # Clear all regions
        for region_item in self.region_items:
            self.plot_widget.removeItem(region_item)
        print("region items to be cleared: \n", self.region_items)
        self.region_items = []
        # Clear all text items
        print("Text items to remove:", len(self.text_items))  # Debugging
        for text_item in self.text_items:
            self.plot_widget.removeItem(text_item)
        self.text_items = []
        # Clear the waveform plot
        if self.curve is not None:
            self.plot_widget.removeItem(self.curve)
            self.curve = None
        # Clear changed data dictionaries
        self.changed_time = {}
        self.plot_widget.update()
        #self.changed_probability = {}

    def handle_label_update(self, region_item, text_item, var, prob, count):
        # Get the current values of the region
        region_values = region_item.getRegion()
        # Calculate the relative label position
        label_x = region_values[0] # + (region_values[1] - region_values[0]) / 2
        print("region value[0]: ", label_x)
        # Update the text item text and position
        text_item.setText(f"{var}\n{prob}\n{count}")
        # Set the text color
        text_item.setColor(pg.mkColor('blue'))
        text_item.setFont(pg.QtGui.QFont("Arial", 15))
        text_item.setPos(label_x, 1)

    def plot_data(self, path):
        column_names = ['end_time', 'probability', 'variable', 'count']
        file = pd.read_csv(path, skiprows=1, header=None, sep=' ', names=column_names)
        # Set the first value of the 'start_time' column to 0
        file['start_time'] = 0
        print("start time = 0: \n", file['start_time'])
        # Shift the 'start_time' values up by one row
        file['start_time'] = file['end_time'].shift(fill_value=0)
        # Convert 'start_time' and 'end_time' to float type
        file['start_time'] = file['start_time'].astype(float)
        file['end_time'] = file['end_time'].astype(float)
        print("start time \t end time \n", file['start_time'], " \t", file['end_time'])
        # Convert 'start_time' and 'end_time' to float type
        file['start_time'] = file['start_time'].astype(float)
        file['end_time'] = file['end_time'].astype(float)
        print("pandas file after mod: \n", file)
        zipp = zip(file['start_time'], file['end_time'], file['variable'], file['probability'], file['count'])
        cells = [create_cells(row) for row in zipp]  
        index = 0
        for cell in cells:
            #swap mode is not working? check
            region_item = LinearRegionItem(values=(cell.st, cell.et,cell.var, cell.prob, cell.count),orientation=pg.LinearRegionItem.Vertical, pen=pg.mkPen(color='k', width=1.5), swapMode='block')
            self.region_items.append(region_item)
            print("appending to region_lst")
            self.region_lst.append([index, [cell.st, cell.et, cell.var, cell.prob, cell.count]])
            print("region item after appending: \n", self.region_lst)
            self.plot_widget.addItem(region_item)
            text_item = pg.TextItem(text=f"{cell.var}\n(Prob: {cell.prob})\n{cell.count}", anchor=(0, 0))
            self.text_items.append(text_item)
            self.plot_widget.addItem(text_item)
            print("main region item:", region_item)
            index += 1
            # Connect the clicked signal of the region item to a slot
            region_item.clicked.connect(self.display_clicked_values)
            # Connect other signals and perform necessary setup
            self.connect_region_signals(region_item, text_item, cell.var, cell.prob, cell.count)
            self.handle_label_update(region_item, text_item, cell.var, cell.prob, cell.count)

        self.plot_widget.setLabel("bottom", text="Time(s)")
        self.plot_widget.getPlotItem().getAxis("bottom").orientation = 'top'
        self.plot_widget.getAxis("bottom").setVisible(True)
        self.plot_widget.getAxis("left").setVisible(True)
        self.plot_widget.setXRange(cells[0].st, cells[-1].et)
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
        start_index = int(start_time * self.sample_rate)
        end_index = int(end_time * self.sample_rate)
        print("start index:", start_index)
        print("end index:", end_index)
        # Extract audio data within the specified start and end time
        audio_segment = self.audio_data[start_index:end_index]
        # Increase buffer size to reduce underruns
        blocksize = 2048  # Experiment with different values to find the optimal buffer size
        print("Sample Rate:", self.sample_rate)
        # Start audio playback
        sd.play(audio_segment, samplerate=self.sample_rate, blocksize=blocksize)
        sd.wait()  # Wait until playback is finished
        # Set the flag to indicate that audio playback has finished
        self.audio_playing = False

    def create_region_item(self, start_time, end_time, variable, probability, count):
        # Create the new region item
        region_item = LinearRegionItem(values=(start_time, end_time, variable, probability, count),
                                    orientation=pg.LinearRegionItem.Vertical,
                                    pen=pg.mkPen(color='k', width=1.5), swapMode='block')
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
        self.region_lst.insert(insert_index, [insert_index, [start_time, end_time, variable, probability, count]])
        # Add the region item to the plot widget
        self.plot_widget.addItem(region_item)
        print(f"New region item created for Variable: {variable}")
        self.plot_widget.addItem(region_item)
        text_item = pg.TextItem(text=f"{variable}\n(Prob: {probability})\n{count}", anchor=(0, 0))
        self.text_items.append(text_item)
        self.plot_widget.addItem(text_item)
        print("Text items of new region: ", self.text_items)
        # Connect the clicked signal of the region item to a slot
        region_item.clicked.connect(self.display_clicked_values)
        self.connect_region_signals(region_item, text_item, variable, probability, count)
        self.handle_label_update(region_item, text_item, variable, probability, count)
        print(f"New region item created for Variable: {variable}")
        # Clear QLineEdit boxes
        self.ui.lineEdit.clear()
        self.ui.lineEdit_6.clear()
        self.ui.lineEdit_3.clear()
        self.ui.lineEdit_4.clear()
        self.ui.lineEdit_5.clear()

    def plot_graph(self, path):
        # Open the audio file and extract data
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
        time = np.linspace(0, num_frames / wave_obj.getframerate(), num_frames)
        #print("time data \n", time)
        amplitude = audio_data.tolist()
        self.audio_len = audio_duration
        print("Audio duration:", audio_duration, "seconds")
        # Create a curve on the first load
        if self.curve is None:
            self.curve = self.plot_widget.plot(name="Audio Waveform", pen='r')
        # Update the curve with the initial audio data
        self.curve.setData(time, amplitude)
        #print("Probability:", probability_text)

    def get_last_y_range(self):
        # Get the y-axis item
        y_axis = self.plot_widget.getAxis("left")
        # Get the current range of the y-axis
        y_range = y_axis.range
        return y_range

    def resizeEvent(self, event):
        # Resize the plot widget along with the central widget
        new_size = event.size()
        self.plot_widget.setGeometry(0, 0, new_size.width(), 750)
        event.accept()

def run_app():
    # Run the GUI tool
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()
