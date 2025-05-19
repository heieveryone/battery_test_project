import tkinter as tk
import battery_detect as bd
from threading import Thread

# 建立主視窗
root = tk.Tk()
root.title("Battery Test 控制介面")
root.geometry("900x600")
default_font = ("Arial", 12)
# --- Control Frame ---
ctrl_frame = tk.LabelFrame(root, text="控制", padx=10, pady=10)
ctrl_frame.grid(row=0, column=0, sticky="nw", padx=10, pady=10)

mode_var = tk.StringVar(value="charge")
charge_rb = tk.Radiobutton(ctrl_frame, text="Charge 模式", variable=mode_var, value="charge")
discharge_rb = tk.Radiobutton(ctrl_frame, text="Discharge 模式", variable=mode_var, value="discharge")
charge_rb.grid(row=0, column=0, sticky='w')
discharge_rb.grid(row=0, column=1, sticky='w')

start_btn = tk.Button(ctrl_frame, text="開始執行", command=lambda: Thread(target=bd.start_all, daemon=True).start())
emergency_btn = tk.Button(ctrl_frame, text="緊急停止", command=lambda: bd.shutdown.set(), state='disabled')
start_btn.grid(row=1, column=0, pady=5)
emergency_btn.grid(row=1, column=1, pady=5)
# 傳初始 mode 給後端
start_btn.config(command=lambda: [bd.set_mode(mode_var.get()), start_btn.config(state='disabled'), charge_rb.config(state='disabled'), discharge_rb.config(state='disabled'), emergency_btn.config(state='normal'), Thread(target=bd.start_all, daemon=True).start(), update_status()])

# --- Status Frame ---
status_frame = tk.LabelFrame(root, text="狀態", padx=10, pady=10)
status_frame.grid(row=1, column=0, sticky="nw", padx=10, pady=10)
status_lbl = tk.Label(status_frame, text="READY", width=15, bg="gray", fg="white")
status_lbl.grid(row=0, column=0, columnspan=2, pady=5)
mode_display_lbl = tk.Label(status_frame, text="目前模式：─")
mode_display_lbl.grid(row=1, column=0, columnspan=2, sticky='w')
charge_count_lbl = tk.Label(status_frame, text="Charge 次數：0")
charge_count_lbl.grid(row=2, column=0, sticky='w')
discharge_count_lbl = tk.Label(status_frame, text="Discharge 次數：0")
discharge_count_lbl.grid(row=2, column=1, sticky='w')

# --- Data Frame ---
data_frame = tk.LabelFrame(root, text="數據顯示", padx=10, pady=10)
data_frame.grid(row=2, column=0, sticky="nw", padx=10, pady=10)
tk.Label(data_frame, text="Voltage:").grid(row=0, column=0, sticky='e')
vol_lbl = tk.Label(data_frame, text="0.000 V")
vol_lbl.grid(row=0, column=1, sticky='w')

tk.Label(data_frame, text="Current:").grid(row=1, column=0, sticky='e')
cur_lbl = tk.Label(data_frame, text="0.000 A")
cur_lbl.grid(row=1, column=1, sticky='w')

tk.Label(data_frame, text="Temp:").grid(row=2, column=0, sticky='e')
temp_lbl = tk.Label(data_frame, text="0.00 °C")
temp_lbl.grid(row=2, column=1, sticky='w')
# --- Instrument Indicators ---
ind_frame = tk.LabelFrame(root, text="儀器狀態指示", padx=10, pady=10)
ind_frame.grid(row=0, column=1, rowspan=3, sticky="ne", padx=10, pady=10)
psu_indicator  = tk.Label(ind_frame, text="PSU",  width=10, bg='gray')
load_indicator = tk.Label(ind_frame, text="LOAD", width=10, bg='gray')
lcr_indicator  = tk.Label(ind_frame, text="LCR",  width=10, bg='gray')
daq_indicator  = tk.Label(ind_frame, text="DAQ",  width=10, bg='gray')
m3_indicator   = tk.Label(ind_frame, text="PLC_M3",   width=10, bg='gray')
m5_indicator   = tk.Label(ind_frame, text="PLC_M5",   width=10, bg='gray')
for w in (psu_indicator, load_indicator, lcr_indicator, daq_indicator, m3_indicator, m5_indicator):
    w.pack(pady=2)
    
# --- EIS Frame ---
# 在建立完 data_frame 之後，增設一個 EIS Frame
eis_frame = tk.LabelFrame(root, text="EIS 數據", padx=10, pady=10)
eis_frame.grid(row=3, column=0, columnspan=2, sticky="nw", padx=10, pady=10)

# 頻率
tk.Label(eis_frame, text="Freq:", font=default_font).grid(row=0, column=0, sticky='e')
freq_lbl = tk.Label(eis_frame, text="— Hz", font=default_font)
freq_lbl.grid(row=0, column=1, sticky='w', padx=5)

# 實部
tk.Label(eis_frame, text="Real:", font=default_font).grid(row=1, column=0, sticky='e')
real_lbl = tk.Label(eis_frame, text="— Ω", font=default_font)
real_lbl.grid(row=1, column=1, sticky='w', padx=5)

# 虛部
tk.Label(eis_frame, text="Imag:", font=default_font).grid(row=2, column=0, sticky='e')
imag_lbl = tk.Label(eis_frame, text="— Ω", font=default_font)
imag_lbl.grid(row=2, column=1, sticky='w', padx=5)

# 釋放多餘空間
root.grid_rowconfigure(3, weight=1)
root.grid_columnconfigure(0, weight=1)


def emergency_stop():
    bd.shutdown.set()

def start_process():
    # 1) 先把 GUI 上選好的初始 mode 直接設定給後端
    bd.set_mode(mode_var.get())       # instrument_control 裡面的 setter
    # 2) 禁用選單、按鈕，避免啟動後再改
    start_btn.config(state='disabled')
    charge_rb.config(state='disabled')
    discharge_rb.config(state='disabled')
    emergency_btn.config(state='normal')
    # 3) 啟動所有儀器控制的 thread
    bd.start_all()                    # 這個會建立 PLC_safe、cycle_thread、DAQ、EIS… 等 daemon threads
    # 4) 啟動畫面更新迴圈
    update_status()

def update_status():
    # 主狀態
    running = not bd.shutdown.is_set()
    status_lbl.config(text="RUNNING" if running else "STOPPED", bg="green" if running else "red")
    # 模式
    with bd.mode_lock:
        m = bd.mode or "─"
    mode_display_lbl.config(text=f"目前模式：{m}")
    # 次數
    charge_count_lbl.config(text=f"Charge 次數：{bd.charge_cycle_count}")
    discharge_count_lbl.config(text=f"Discharge 次數：{bd.discharge_cycle_count}")
    # 數據
    vol_lbl.config(text=f"{bd.latest_voltage:.3f} V")
    cur_lbl.config(text=f"{bd.latest_current:.3f} A")
    temp_lbl.config(text=f"{bd.latest_temperature:.2f} °C")
    # EIS
    if bd.latest_eis:
        freq, real_val, imag_val = bd.latest_eis
        f = float(freq.strip())
        freq_lbl.config(text=f"{f:.3f} Hz")
        real_lbl.config(text=f"{real_val:.3f} Ω")
        imag_lbl.config(text=f"{imag_val:.3f} Ω")
    else:
        # 沒值就給預設
        freq_lbl.config(text="— Hz")
        real_lbl.config(text="— Ω")
        imag_lbl.config(text="— Ω")
    # 指示燈
    psu_indicator.config(bg='green' if bd.instrument_flags['psu'] else 'gray')
    load_indicator.config(bg='green' if bd.instrument_flags['load'] else 'gray')
    lcr_indicator.config(bg='green' if bd.instrument_flags['lcr'] else 'gray')
    daq_indicator.config(bg='green' if bd.instrument_flags['daq'] else 'gray')
    m3_indicator.config(bg='red'   if bd.instrument_flags['plc_m3']  else 'gray')
    m5_indicator.config(bg='red'   if bd.instrument_flags['plc_m5']  else 'gray')
    if not bd.shutdown.is_set():
        root.after(500, update_status)

# 關閉時停止儀器
root.protocol("WM_DELETE_WINDOW", lambda: bd.shutdown.set() or root.destroy())

root.mainloop()