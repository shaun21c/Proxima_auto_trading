import sys
import pandas as pd

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5 import uic


# main.ui 파일을 로드하여 form_class에 저장
form_class = uic.loadUiType(r"99 main.ui")[0]

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCound(self, parent = None):
        return self._data.shape[0]
    
    def columnCount(self, parent = None):
        return self._data.shape[1]
    
    def data(self, index, role = Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None
    
    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[section]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return self._data.index[section]
        return None
    
    def setData(self, index, value, role):
        #항상 False를 반환하여 편집을 활성화
        return False
    
    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

# QMainWindow를 상속받아 form_class를 사용하는 QtDesignerExample 클래스를 정의
class QtDesignerExample(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.show()

        # 버튼을 누르면 button_clicked 메소드가 호출, 버튼을 추가할때 마다 이벤트를 연결해주어야 함
        self.myPushButton.clicked.connect(self.button_clicked)

    def button_clicked(self):
        """버튼을 눌렀을 때 호출되는 메소드"""
        # 라벨과 라인에디트에 텍스트 설정
        self.myLabel.setText("button_clicked")
        self.myLineEdit.setText("2024-05-18")
        # 콤보박스에 아이템 추가
        self.myComboBox.addItems(["2024-05-18", "2024-05-17", "2024-05-16"])
        sample_df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
        pd_model = PandasModel(sample_df)
        self.myTableView.setModel(pd_model)
        print(self.myLabel.text())
        print(self.myLineEdot.text())
        print(self.myComboBox.currentText())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qt_designer_example = QtDesignerExample()
    sys.exit(app.exec_())