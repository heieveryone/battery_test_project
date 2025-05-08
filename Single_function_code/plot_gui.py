import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QPushButton, QWidget, QLabel, QListWidget, QAbstractItemView, QCheckBox, QHBoxLayout, QRadioButton, QButtonGroup, QSpacerItem, QSizePolicy
from PyQt5 import Qt

class CSVPlotter(QMainWindow):
    #繼承QMainWindow的初始化屬性，及初始化自訂的initUI()
    def __init__(self):
        super().__init__()
        self.initUI()
    #自訂UI
    def initUI(self):
        #初始主布局架構
        self.setWindowTitle('CSV Plotter') #視窗名稱
        self.central_widget = QWidget(self) #創建中央widget
        self.setCentralWidget(self.central_widget) #設置中央widget
        self.layout = QVBoxLayout(self.central_widget) #設置中央widget布局為垂直布局
        #創建元件
        self.label = QLabel('選擇一個資料夾以選取CSV檔', self) #創建label
        self.layout.addWidget(self.label) #將元件加入widget
        self.button = QPushButton('選擇資料夾', self) #創建button
        self.button.clicked.connect(self.openFolder) #將button訊號連接函式
        self.layout.addWidget(self.button) #將元件加入widget
        self.listWidget = QListWidget(self) #創建list顯示元件
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection) #可選擇複數
        self.layout.addWidget(self.listWidget) #將元件加入widget
            # Add radio buttons for charge/discharge selection
        self.radio_layout = QHBoxLayout() #創建水平布局
            #創建單選button
        self.charge_radio = QRadioButton('Charge') 
        self.discharge_radio = QRadioButton('Discharge')
            #組合單選button
        self.charge_discharge_group = QButtonGroup()
        self.charge_discharge_group.addButton(self.charge_radio)
        self.charge_discharge_group.addButton(self.discharge_radio)
            #添加間隔
        self.radio_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.radio_layout.addWidget(self.charge_radio)
        self.radio_layout.addWidget(self.discharge_radio)
        self.radio_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
            # Create container layout for radio buttons，創建垂直子布局，並添加水平布局
        self.radio_container = QVBoxLayout()
        self.radio_container.addLayout(self.radio_layout)
            # Add checkboxes
        self.checkbox_layout = QHBoxLayout() #創建水平布局
            #創建核選方塊
        self.voltage_checkbox = QCheckBox('Voltage', self)
        self.current_checkbox = QCheckBox('Current', self)
        self.resistance_checkbox = QCheckBox('Resistance', self)
        self.temperature_checkbox = QCheckBox('Temperature', self)
            #添加間隔
        self.checkbox_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.checkbox_layout.addWidget(self.voltage_checkbox)
        self.checkbox_layout.addWidget(self.current_checkbox)
        self.checkbox_layout.addWidget(self.resistance_checkbox)
        self.checkbox_layout.addWidget(self.temperature_checkbox)
        self.checkbox_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
            # Create container layout for checkboxes，創建垂直子布局，並添加水平布局
        self.checkbox_container = QVBoxLayout()
        self.checkbox_container.addLayout(self.checkbox_layout)
            # Add container layouts between QListWidget and plot button，在主布局中加入，子布局
        self.layout.addLayout(self.radio_container)
        self.layout.addLayout(self.checkbox_container)
            #創建按鈕
        self.plotButton = QPushButton('繪製單一圖片', self)
        self.plotButton.clicked.connect(self.plotCSVCombined)
        self.layout.addWidget(self.plotButton)
        self.plotSeparateButton = QPushButton('分別繪製圖片', self)
        self.plotSeparateButton.clicked.connect(self.plotCSVSeparate)
        self.layout.addWidget(self.plotSeparateButton)
    #動作函式
    def openFolder(self):
        folder = QFileDialog.getExistingDirectory(self, '選擇資料夾') #此函式會打開文件夾選擇框，並返回選擇的文件夾路徑，如取消，返回空字串
        #檢查是否選擇文件夾
        if folder:
            self.listWidget.clear() #清空listWidget，移除現有項目
            self.folder = folder #self儲存選擇文件夾的路徑，方便後面調用
            for filename in os.listdir(folder):
                if filename.endswith('.csv'):
                    self.listWidget.addItem(filename) #將文件夾添加到listWidget中
    def csv_type(self): #確認選擇方塊的性質
        if self.charge_radio.isChecked():
            state = 'Charge'
        elif self.discharge_radio.isChecked():
            state = 'Discharge'
        else:
            state = ''
        voltage = self.voltage_checkbox.isChecked()
        current = self.current_checkbox.isChecked()
        resistance = self.resistance_checkbox.isChecked()
        temperature = self.temperature_checkbox.isChecked()
        return state, voltage, current, resistance, temperature
    def plotCSVCombined(self): #繪製數據結合的圖片
        file_paths = []
        data_frames = []
        selected_files = [item.text() for item in self.listWidget.selectedItems()] #列表生成式，直接得到一個文件名的list
        #將檔案路徑添加入list
        for file in selected_files:
            file_paths.append(os.path.join(self.folder, file))
        data_frames = read_csv_files(file_paths) #讀取檔案內容，並存入list中
        state, voltage, current, resistance, temperature = self.csv_type() #獲取csv屬性
        plot_data(data_frames, state, voltage, current, resistance, temperature, combined=True) #繪圖
    
    def plotCSVSeparate(self): #繪製數據分開的圖片
        selected_files = [item.text() for item in self.listWidget.selectedItems()]
        for file in selected_files:
            file_path = os.path.join(self.folder, file)
            data_frame = read_csv_files([file_path])[0]  # 從list內讀取第一個數據(也是唯一一個)
            state, voltage, current, resistance, temperature = self.csv_type()
            plot_data([data_frame], state, voltage, current, resistance, temperature, combined=False)
            plt.title(file)  # Add file name as title
#將csv資料讀取，並計算時間差，按順序存入list中
def read_csv_files(file_paths):
    data_frames = []
    for file_path in file_paths:
        df = pd.read_csv(file_path)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        # 將 Timestamp 轉換為只包含時間的 timedelta
        df['TimeDelta'] = df['Timestamp'] - df['Timestamp'].iloc[0]
        data_frames.append(df)
    return data_frames
#計算總時間
def calculate_total_duration(data_frames):
    all_times = pd.concat([df['TimeDelta'] for df in data_frames])
    total_duration = all_times.max() - all_times.min()
    return total_duration
#繪製圖片
def plot_data(data_frames, state, voltage, current, resistance, temperature, combined = True):
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']  # 可用顏色列表
    linestyles = ['-', '--', '-.', ':']  # 線條樣式列表
    if combined: #確認是否結合指令
        plt.figure(figsize=(15, 5))
        color_index = 0
        linestyle_index = 0
        
        for i, df in enumerate(data_frames): #enumerate函數可以獲得list中元素的索引(i)和值(df)
            if voltage:
                plt.plot(df['TimeDelta'].dt.total_seconds() / 3600, df['Voltage'], 
                         label=f'Voltage - cycle {i+1}', color=colors[color_index % len(colors)], 
                         linestyle=linestyles[linestyle_index % len(linestyles)])
                plt.ylabel('Voltage (V)')
                color_index += 1
                linestyle_index += 1
            
            if current:
                plt.plot(df['TimeDelta'].dt.total_seconds() / 3600, df['Current'], 
                         label=f'Current - cycle {i+1}', color=colors[color_index % len(colors)], 
                         linestyle=linestyles[linestyle_index % len(linestyles)])
                plt.ylabel('Current (A)')
                color_index += 1
                linestyle_index += 1
            
            if resistance:
                plt.plot(df['TimeDelta'].dt.total_seconds() / 3600, df['Resistance_mOhm'], 
                         label=f'Resistance - cycle {i+1}', color=colors[color_index % len(colors)], 
                         linestyle=linestyles[linestyle_index % len(linestyles)])
                plt.ylabel('Resistance (mΩ)')
                color_index += 1
                linestyle_index += 1
            
            if temperature:
                plt.plot(df['TimeDelta'].dt.total_seconds() / 3600, df['Temperature'], 
                         label=f'Temperature - cycle {i+1}', color=colors[color_index % len(colors)], 
                         linestyle=linestyles[linestyle_index % len(linestyles)])
                plt.ylabel('Temperature (°C)')
                color_index += 1
                linestyle_index += 1
        
        plt.xlabel('Time (hours)')
        plt.title(f'Battery {state} Data (Combined)')
        plt.legend() #顯示圖例(label)
        plt.grid(True)
        plt.xlim(0, 2.5 if state == "Charge" else 0.1)
        plt.gca().xaxis.set_major_locator(plt.MultipleLocator(0.01)) #設置x軸刻度，gca()獲取當前座標軸
        plt.gcf().autofmt_xdate() #格式化x軸上的日期標籤
        plt.show()
    else: #分開繪製
        for i, df in enumerate(data_frames):
            plt.figure(figsize=(10, 6))
            if voltage:
                plt.plot(df['TimeDelta'].dt.total_seconds() / 3600, df['Voltage'], 
                         label='Voltage', color=colors[i % len(colors)])
                plt.ylabel('Voltage (V)')
            if current:
                plt.plot(df['TimeDelta'].dt.total_seconds() / 3600, df['Current'], 
                         label='Current', color=colors[i % len(colors)])
                plt.ylabel('Current (A)')
            if resistance:
                plt.plot(df['TimeDelta'].dt.total_seconds() / 3600, df['Resistance_mOhm'], 
                         label='Resistance', color=colors[i % len(colors)])
                plt.ylabel('Resistance (mΩ)')
            if temperature:
                plt.plot(df['TimeDelta'].dt.total_seconds() / 3600, df['Temperature'], 
                         label='Temperature', color=colors[i % len(colors)])
                plt.ylabel('Temperature (°C)')
            
            plt.xlabel('Time (hours)')
            plt.title(f'{state} Data - Cycle {i+1}')
            plt.legend()
            plt.grid(True)
            plt.xlim(0, 2.5 if state == "Charge" else 1)
            plt.gca().xaxis.set_major_locator(plt.MultipleLocator(0.1))
            plt.gcf().autofmt_xdate()
            plt.show()
if __name__ == '__main__': #如果執行此程式
    app = QApplication(sys.argv)
    ex = CSVPlotter()
    ex.show()
    sys.exit(app.exec_())