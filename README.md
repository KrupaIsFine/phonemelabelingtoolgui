# Phoneme-Level-Labeling-Tool-GUI

This is a Phoneme-Level-Labeling-Tool developed using PyQt5 for annotating the dataset (.lab files generated from HSA) and boundary correcting the audio waveform with respect to its phonetic sounds.
Please refer the GUI Demo video file provided to visually understand the tool's functionality.

Steps:
------
Installation
------------
1. Install Miniconda/Anaconda. Create a new conda virtual environment
```
   conda create -n <env-name>
```
2. Activate your new environment
```
   conda activate <env-name>
```
3. Install the required packages
```
   conda install pip
   pip install PyQt5==5.15.10
   pip install pyqtgraph==0.13.3
   pip install sounddevice==0.4.6
```

Executing the Code
------------------
1. Run the labelingtool.py from terminal
```
    python3 labelingtool.py
```
2. Load the .wav file and .lab file into the GUI with 'Load Audio' and 'Load Dataset' buttons
3. Refer to the video demo of the GUI for understanding the flow and functionality of the GUI
