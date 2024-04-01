# Phoneme-Level-Labeling-Tool-GUI

This is a Phoneme-Level-Labeling-Tool developed using PyQt5 for annotating the dataset (.lab files generated from HSA) and boundary correcting the audio waveform with respect to its phonetic sounds.
Please refer the GUI Demo video file provided to visually understand the tool's functionality.

Steps:
------
Installation
------------
1. Create a Python Virtual Environment [opt. Install Miniconda/Anaconda. Create a new conda virtual environment]
```
   python -m venv <env-name>
```
2. Activate your new environment
   [Linux]
```
   source <env-name>/bin/activate
```
3. Install the required packages
```
   pip install numpy pandas librosa sounddevice pyqt5 pyqtgraph
```

Executing the Code
------------------
1. Run the labelingtool.py from terminal
```
    python3 labelingtool.py
```
2. Load the .wav file and .lab file into the GUI with 'Load Audio' and 'Load Dataset' buttons
3. Refer to the video demo of the GUI for understanding the flow and functionality of the GUI
