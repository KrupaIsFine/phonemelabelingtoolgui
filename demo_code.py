# # Reference selection code

# from PyQt5.QtCore import *
# from PyQt5.QtGui import *
# from PyQt5.QtWidgets import *
# import sys
# # class Boton(QGraphicsItem):
# #     def __init__(self,parent,size,X,Y,name):
# #         super(Boton,self).__init__()
# #         self.setFlag(QGraphicsItem.ItemIsSelectable, True)        
# #         self.parent=parent
# #         self.globalRec=QRectF(0,0,size,size)
# #         self.setPos(X,Y)
# #         self.parent._scene.addItem(self)
# #     def cambi(self,val):
# #         self.setSelected(val)
# #     def paint(self,painter,option,widget):
# #         if not self.isSelected():
# #             painter.setBrush(self.parent.brush2)
# #         if self.isSelected():
# #             painter.setBrush(self.parent.brush1)       
# #         painter.setPen(self.parent.pen)
# #         painter.drawEllipse(self.globalRec)
# #     def boundingRect(self):
# #         return self.globalRec
# class Viewer(QGraphicsView):
#     rectChanged = pyqtSignal(QRect)
#     def __init__(self, parent):
#         super(Viewer, self).__init__(parent)
#         self.select=0   
#         self.misItems=None
#         color2 = QColor(5,100,70)
#         color3 = QColor(155,100,70)
#         color1 = QColor(225,100,70)
#         self.brush1=QBrush(color1)
#         self.brush2=QBrush(color2)
#         self.origin = QPoint()
#         self.poi=QPoint()
#         self.pen=QPen()        
#         self.pen.setWidth(2)
#         self.pen.setColor(color3)
#         self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
#         self.setMouseTracking(True)
#         self.changeRubberBand = False
#         self._scene = QGraphicsScene(self)
#         self.setScene(self._scene)
#         # Boton(self,20,0,0,'btn1')
#         # Boton(self,20,0,80,'btn2')
#         # Boton(self,20,0,-80,'btn3')

#     def mousePressEvent(self, event):
#         if event.button() == Qt.LeftButton:
#             self.origin = event.pos()
#             self.rubberBand.setGeometry(QRect(self.origin, QSize(0, 0)))
#             self.rectChanged.emit(self.rubberBand.geometry())
#             self.rubberBand.show()
#             self.changeRubberBand = True
#             return
#         super(Viewer, self).mousePressEvent(event)
#     def mouseMoveEvent(self, event):
#         if self.changeRubberBand:
#             self.rubberBand.setGeometry(
#                 QRect(self.origin, event.pos()).normalized())
#             self.rectChanged.emit(self.rubberBand.geometry())
#         super(Viewer, self).mouseMoveEvent(event)
#     def mouseReleaseEvent(self, event):
#         if event.button() == Qt.LeftButton:
#             self.changeRubberBand = False
#             if self.rubberBand.isVisible():
#                 self.rubberBand.hide()
#                 rect = self.rubberBand.geometry()
#                 rect_scene = self.mapToScene(rect).boundingRect()
#                 selected = self.scene().items(rect_scene)
                
#                 if self._scene.selectedItems():
#                     self._scene.clearSelection()
                
# #event SELECT items Buttons:
#                 # Deselect previously selected items.
#                 if selected:
#                     self.misItems=selected
#                     for item in selected:
#                         item.cambi(True)               
#         super(Viewer, self).mouseReleaseEvent(event)


# class Window(QWidget):
#     def __init__(self):
#         super(Window, self).__init__()
#         self.viewer = Viewer(self)
#         VBlayout = QVBoxLayout(self)
#         VBlayout.addWidget(self.viewer)
#         VBlayout.setContentsMargins(0,0,0,0)
#         self.setFixedSize(400,400)
# if __name__ == "__main__":
#     import sys
#     app = QApplication(sys.argv)
#     window = Window()
#     window.show()
#     sys.exit(app.exec_())



import sys
from PyQt5 import QtWidgets, uic

# Import the Ui_MainWindow class generated from the UI file
from demo import Ui_MainWindow

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Set up the user interface from Designer
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Any additional setup code can go here

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())