import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import battery_detect as bd
from threading import Thread

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGroupBox, QRadioButton, QPushButton,
    QLabel, QGridLayout, QVBoxLayout, QHBoxLayout, QSizePolicy, QTextEdit,
    QListWidget, QFileDialog, QAbstractItemView, QCheckBox, QButtonGroup
)
from PyQt5.QtCore import QTimer, Qt, QObject, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

# Redirect print() to GUI log
class EmittingStream(QObject):
    text_written = pyqtSignal(str)
    def __init__(self): super().__init__()
    def write(self, text):
        if text:
            self.text_written.emit(str(text))
    def flush(self): pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Battery Test 控制介面")
        self.resize(1200, 800)
        fnt = QFont("Arial", 12)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QGridLayout(central)
        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 2)

        # --- Control Panel ---
        ctrl = QGroupBox("控制")
        v1 = QVBoxLayout(ctrl)
        self.rb_c = QRadioButton("Charge 模式"); self.rb_c.setFont(fnt)
        self.rb_d = QRadioButton("Discharge 模式"); self.rb_d.setFont(fnt)
        self.rb_c.setChecked(True)
        v1.addWidget(self.rb_c); v1.addWidget(self.rb_d)
        self.btn_start = QPushButton("開始執行"); self.btn_start.setFont(fnt)
        self.btn_stop  = QPushButton("緊急停止"); self.btn_stop.setFont(fnt)
        self.btn_stop.setEnabled(False)
        v1.addWidget(self.btn_start); v1.addWidget(self.btn_stop)
        layout.addWidget(ctrl, 0, 0)

        # --- Instrument Indicators ---
        ind = QGroupBox("儀器狀態指示")
        v2 = QVBoxLayout(ind)
        self.inds = {}
        for name in ['psu','load','lcr','daq','plc_m3','plc_m5']:
            lbl = QLabel(name.upper()); lbl.setFont(fnt); lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background: gray;"); lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            v2.addWidget(lbl)
            self.inds[name] = lbl
        layout.addWidget(ind, 0, 1, 4, 1)

        # --- Status Panel ---
        st = QGroupBox("狀態")
        v3 = QVBoxLayout(st)
        self.lbl_run  = QLabel("READY"); self.lbl_run.setFont(fnt)
        self.lbl_run.setAlignment(Qt.AlignCenter); self.lbl_run.setStyleSheet("background: gray; color: white;")
        v3.addWidget(self.lbl_run)
        self.lbl_mode = QLabel("目前模式：─"); self.lbl_mode.setFont(fnt); v3.addWidget(self.lbl_mode)
        hcount = QHBoxLayout()
        self.lbl_cct = QLabel("Charge 次數：0"); self.lbl_cct.setFont(fnt)
        self.lbl_dct = QLabel("Discharge 次數：0"); self.lbl_dct.setFont(fnt)
        hcount.addWidget(self.lbl_cct); hcount.addWidget(self.lbl_dct)
        v3.addLayout(hcount)
        self.lbl_first = QLabel("初次放電容量：— Ah"); self.lbl_first.setFont(fnt)
        self.lbl_last  = QLabel("上一筆放電容量：— Ah"); self.lbl_last.setFont(fnt)
        self.lbl_pct   = QLabel("容量變化：— %"); self.lbl_pct.setFont(fnt)
        v3.addWidget(self.lbl_first); v3.addWidget(self.lbl_last); v3.addWidget(self.lbl_pct)
        layout.addWidget(st, 1, 0)

        # --- Data Panel ---
        dt = QGroupBox("DAQ數據顯示")
        g = QGridLayout(dt)
        self.dvals = []
        for i, txt in enumerate(["Voltage:", "Current:", "Temp:"]):
            g.addWidget(QLabel(txt), i, 0)
            val = QLabel("0.000"); val.setFont(fnt)
            g.addWidget(val, i, 1); self.dvals.append(val)
        layout.addWidget(dt, 2, 0)

        # --- EIS Panel ---
        eis = QGroupBox("EIS 數據")
        ge = QGridLayout(eis)
        self.evals = []
        for i, txt in enumerate(["Freq:", "Real:", "Imag:"]):
            ge.addWidget(QLabel(txt), i, 0)
            v = QLabel("—"); v.setFont(fnt); ge.addWidget(v, i, 1); self.evals.append(v)
        layout.addWidget(eis, 3, 0)

        # --- CSV Plotter & EIS Plotter Panel ---
        pg = QGroupBox("檔案及繪圖")
        pg_layout = QVBoxLayout(pg)
        # CSV Plotter
        pg_layout.addWidget(QLabel('CSV Plotter', font=fnt))
        self.folder_btn = QPushButton("選擇CSV資料夾"); self.folder_btn.setFont(fnt)
        self.folder_btn.clicked.connect(self.open_folder)
        pg_layout.addWidget(self.folder_btn)
        self.listWidget = QListWidget(); self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        # Add radio buttons for charge/discharge selection
        self.radio_layout = QHBoxLayout() #創建水平布局
        #創建單選button
        self.charge_radio = QRadioButton('Charge') 
        self.discharge_radio = QRadioButton('Discharge')
        #組合單選button
        self.charge_discharge_group = QButtonGroup()
        self.charge_discharge_group.addButton(self.charge_radio)
        self.charge_discharge_group.addButton(self.discharge_radio)
        # Add checkboxes(選擇要繪製的數據)
        self.checkbox_layout = QHBoxLayout() #創建水平布局
        #創建核選方塊
        self.voltage_checkbox = QCheckBox('Voltage', self)
        self.current_checkbox = QCheckBox('Current', self)
        self.resistance_checkbox = QCheckBox('Resistance', self)
        self.temperature_checkbox = QCheckBox('Temperature', self)
        pg_layout.addLayout(self.checkbox_layout)
        # Add list widget
        pg_layout.addWidget(self.listWidget)
        self.plot_btn = QPushButton('繪製CSV合併'); self.plot_sep_btn = QPushButton('分別繪製CSV')
        self.plot_btn.clicked.connect(self.plotCSVCombined)
        self.plot_sep_btn.clicked.connect(self.plotCSVSeparate)
        pg_layout.addWidget(self.plot_btn); pg_layout.addWidget(self.plot_sep_btn)
        # EIS Plotter
        pg_layout.addSpacing(20)
        pg_layout.addWidget(QLabel('EIS Plotter', font=fnt))
        self.eis_btn = QPushButton('繪製EIS圖'); self.eis_btn.setFont(fnt)
        self.eis_btn.clicked.connect(self.plotEIS)
        pg_layout.addWidget(self.eis_btn)
        layout.addWidget(pg, 0, 2, 5, 1)

        # --- Log Output ---
        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.log, 5, 0, 1, 3)

        # Connections
        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(lambda: bd.shutdown.set())

        # Timer
        self.timer = QTimer(self); self.timer.setInterval(500); self.timer.timeout.connect(self.update)

        # Redirect prints
        self.emitter = EmittingStream(); self.emitter.text_written.connect(self.append_log)
        sys.stdout = self.emitter; sys.stderr = self.emitter

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '選擇資料夾')
        if folder:
            self.listWidget.clear(); self.folder = folder
            for fn in os.listdir(folder):
                if fn.lower().endswith('.csv'): self.listWidget.addItem(fn)
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
    
    def plotCSVCombined(self):
        if not hasattr(self, 'folder'): return
        files = [item.text() for item in self.listWidget.selectedItems()]
        if not files: return
        dfs = []
        for f in files:
            path = os.path.join(self.folder, f)
            try:
                df = pd.read_csv(path)
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df['Elapsed_h'] = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds()/3600
                dfs.append((f, df))
            except Exception as e:
                print(f"讀取 {f} 時出錯: {e}")
        plt.figure(figsize=(10,4))
        for name, df in dfs:
            if 'Voltage' in df.columns:
                plt.plot(df['Elapsed_h'], df['Voltage'], label=f)
                plt.xlabel('Time (h)'); plt.ylabel('Voltage (V)')
                plt.title('合併繪圖 - Voltage')
                plt.legend(); plt.grid(True); plt.show(block=False)
            if 'Current' in df.columns:
                plt.plot(df['Elapsed_h'], df['Current'], label=f)
                plt.xlabel('Time (h)'); plt.ylabel('Current (A)')
                plt.title('合併繪圖 - Current')
                plt.legend(); plt.grid(True); plt.show(block=False)
            if 'Resistance' in df.columns:
                plt.plot(df['Elapsed_h'], df['Resistance'], label=f)
                plt.xlabel('Time (h)'); plt.ylabel('Resistance (Ω)')
                plt.title('合併繪圖 - Resistance')
                plt.legend(); plt.grid(True); plt.show(block=False)
            if 'Temperature' in df.columns:
                plt.plot(df['Elapsed_h'], df['Temperature'], label=f)
                plt.xlabel('Time (h)'); plt.ylabel('Temperature (°C)')
                plt.title('合併繪圖 - Temperature')
                plt.legend(); plt.grid(True); plt.show(block=False) 
    def plotCSVSeparate(self):
        if not hasattr(self, 'folder'): return
        files = [item.text() for item in self.listWidget.selectedItems()]
        for f in files:
            path = os.path.join(self.folder, f)
            try:
                df = pd.read_csv(path)
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df['Elapsed_h'] = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds()/3600
                plt.figure(figsize=(8,4))
                if 'Voltage' in df.columns:
                    plt.plot(df['Elapsed_h'], df['Voltage'], label='Voltage')
                if 'Current' in df.columns:
                    plt.plot(df['Elapsed_h'], df['Current'], label='Current')
                if 'Resistance' in df.columns:
                    plt.plot(df['Elapsed_h'], df['Resistance'], label='Resistance')
                if 'Temperature' in df.columns:
                    plt.plot(df['Elapsed_h'], df['Temperature'], label='Temperature')
                plt.xlabel('Time (h)'); plt.legend(); plt.title(f+' 分開繪圖'); plt.grid(True); plt.show(block=False)
            except Exception as e:
                print(f"讀取 {f} 時出錯: {e}")

    def plotEIS(self):
        path, _ = QFileDialog.getOpenFileName(self, '選擇EIS CSV', '', 'CSV Files (*.csv)')
        if not path: return
        df = pd.read_csv(path)
        df['Zmag'] = np.sqrt(df['Zreal']**2 + df['Zimag']**2)
        df['Zphase'] = np.degrees(np.arctan2(df['Zimag'], df['Zreal']))
        # Nyquist
        plt.figure(figsize=(10,4))
        plt.subplot(1,2,1)
        plt.plot(df['Zreal'], -df['Zimag'], 'o-')
        plt.xlabel('Real (Ω)'); plt.ylabel('-Imag (Ω)'); plt.title('Nyquist')
        plt.axis('equal'); plt.grid(True)
        # Bode
        plt.subplot(2,2,2)
        plt.semilogx(df['Frequency (Hz)'], 20*np.log10(df['Zmag'])); plt.title('Bode Mag'); plt.grid(True)
        plt.subplot(2,2,4)
        plt.semilogx(df['Frequency (Hz)'], df['Zphase']); plt.title('Bode Phase'); plt.grid(True)
        plt.tight_layout(); plt.show(block=False)

    def append_log(self, text):
        self.log.moveCursor(QTextCursor.End); self.log.insertPlainText(text); self.log.moveCursor(QTextCursor.End)

    def start(self):
        mode = 'charge' if self.rb_c.isChecked() else 'discharge'
        bd.set_mode(mode)
        self.btn_start.setEnabled(False); self.rb_c.setEnabled(False); self.rb_d.setEnabled(False)
        self.btn_stop.setEnabled(True)
        Thread(target=bd.start_all, daemon=True).start(); self.timer.start()

    def update(self):
        run = not bd.shutdown.is_set()
        self.lbl_run.setText("RUNNING" if run else "STOPPED")
        self.lbl_run.setStyleSheet(f"background: {'green' if run else 'red'}; color: white;")
        with bd.mode_lock: cur = bd.mode or '─'
        self.lbl_mode.setText(f"目前模式：{cur}")
        self.lbl_cct.setText(f"Charge 次數：{bd.charge_cycle_count}")
        self.lbl_dct.setText(f"Discharge 次數：{bd.discharge_cycle_count}")
        caps=bd.discharge_capacities
        if caps:
            f0,last=caps[0],caps[-1]
            pct=(last/f0*100) if f0 else 0
            self.lbl_first.setText(f"初次放電容量：{f0:.3f} Ah"); self.lbl_last.setText(f"上一筆放電容量：{last:.3f} Ah"); self.lbl_pct.setText(f"容量變化：{pct:.1f} %")
        else:
            self.lbl_first.setText("初次放電容量：— Ah"); self.lbl_last.setText("上一筆放電容量：— Ah"); self.lbl_pct.setText("容量變化：— %")
        self.dvals[0].setText(f"{bd.latest_voltage:.3f} V"); self.dvals[1].setText(f"{bd.latest_current:.3f} A"); self.dvals[2].setText(f"{bd.latest_temperature:.2f} °C")
        le=bd.latest_eis
        if le and len(le)==3:
            f,r,i=le; self.evals[0].setText(f"{f:.6f} Hz"); self.evals[1].setText(f"{r:.3f}"); self.evals[2].setText(f"{i:.3f}")
        else:
            for w in self.evals: w.setText("—")
        for k,l in self.inds.items(): l.setStyleSheet(f"background: {'green' if bd.instrument_flags.get(k) else 'gray'};")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow(); w.show(); sys.exit(app.exec_())
