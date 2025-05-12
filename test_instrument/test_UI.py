import time
import pandas as pd
import instrument
import threading
from queue import Queue
import os
import tkinter as tk
from threading import Thread

# --- 全域變數與事件定義（與原始程式相同） ---
DVP_12SE = instrument.DVP_PLC('COM3', '12SE')
time.sleep(0.5)
PDS20_36A = instrument.power_supply("ASRL16::INSTR", "PDS20")
time.sleep(0.5)
Rigol_load = instrument.dc_electronic_load('USB0::0x1AB1::0x0E11::DL3A260500107::INSTR', 'DL3021')
Rigol_load.static_function('CURR')
Rigol_load.static_CC_mode_curr_range(40)
curr = Rigol_load.static_CC_mode_curr_set(5.2)
time.sleep(0.5)
DAQ_970a = instrument.DAQ("USB0::0x2A8D::0x5101::MY58017225::INSTR", "970a")
DAQ_970a.channel_function("VOLT:DC", 10, 101)
DAQ_970a.channel_function("TEMP:TCouple", 'J', 102)
DAQ_970a.channel_function("VOLT:DC", "100mV", 111)
DAQ_970a.channel_scan_config("(@101, 102, 111)", 1, 0.035)
time.sleep(0.5)
LCR_ZM2371 = instrument.LCR("USB0::0x0D4A::0x0016::9429358::INSTR", "ZM2371")
LCR_ZM2371.timeout()
LCR_ZM2371.measure_config("OFF", "BUS", "ON", "LONG", "OFF")
LCR_ZM2371.measure_parameter("REAL", "IMAG")
LCR_ZM2371.measure_source("VOLT", 0.01, 0)
time.sleep(0.5)

# 控制事件與旗標
DAQ_Start_event = threading.Event()
PSU_off_event = threading.Event()
stop_event = threading.Event()
shutdown = threading.Event()
DAQ_ON_event = threading.Event()
charge_OR_discharge_finish_event = threading.Event()
eis_shutdown_flag = threading.Event()
M3_M5_trigger = Queue()
charge_or_discharge_flag = Queue()
mode_lock = threading.Lock()

target_Y0_ON = str(b':01010101FC\r\n')
target_Y0_OFF = str(b':01010100FD\r\n')
target_M2_ON = str(b':01010103FA\r\n')
target_M2_OFF = str(b':01010102FB\r\n')
target_M3_ON = str(b':01010103FA\r\n')
target_M3_OFF = str(b':01010102FB\r\n')
target_M5_ON = str(b':01010105F8\r\n')
target_M5_OFF = str(b':01010104F9\r\n')
# 資料收集相關
def make_empty_df(channel, name):
    cols = ['Channel','Timestamp'] + ([name] if name=='Temperature' else [{101:'Voltage',111:'Current'}[channel]]) + ['Year','Month','Day','Hour','Minute','Second']
    return pd.DataFrame(columns=cols)

df_101 = make_empty_df(101, 'Voltage')
df_102 = make_empty_df(102, 'Temperature')
df_111 = make_empty_df(111, 'Current')
discharge_capacities = []

# 閾值與計數器
charge_VOLtage_LOW, charge_VOLtage_HIGH = 4.10, 4.11
charge_CURRENT_THRESH = 0.052
discharge_voltage_LOW, discharge_voltage_HIGH = 3.9, 3.91
charge_cycle_count = 0
discharge_cycle_count = 0
# UI 需要用到的最新DAQ數值與狀態
latest_voltage = 0.0
latest_current = 0.0
latest_temperature = 0.0
daq_active = False
# --- 其他函式（PLC_safe, cycle_thread, charge_discharge_mode, DAQ, LCR_EIS_sweep）---
#    這裡省略，保持與原始程式完全相同，只是把原先的 input()/print("啟動模式") 相關片段拿掉，
#    並將所有對 global mode 的讀寫都改為透過下面的 mode 變數存取。

mode = None
def PLC_safe():
    M2_ON = DVP_12SE.M2_ON(b':01050802FF00F1\r\n')
    M2_state = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
    if M2_state == target_M2_ON:
        print("M2 open")
    try:
        while not shutdown.is_set():
            M3_state = DVP_12SE.M3_state_read(b':010108030001F2\r\n')  # read M3
            M5_state = DVP_12SE.M5_state_read(b':010108050001F0\r\n')  # read M5
            #print(M3_state, M5_state)
            if M3_state == str(b':01010103FA\r\n'):
                PSU_output = PDS20_36A.output(0)
                DAQ_970a.scan_stop()
                print("discharge and under voltage")
                M3_M5_trigger.put("M3")
                stop_event.set()
                #M2_OFF = DVP_12SE.M2_ON(b':010508020000F0\r\n')
                M2_state = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
                print("M3 stop", M2_state)
                time.sleep(0.1)
                shutdown.set()
            
            if M5_state == str(b':01010105F8\r\n'):
                PSU_output = PDS20_36A.output(0)
                DAQ_970a.scan_stop()
                print("charge and over voltage")
                M3_M5_trigger.put("M5")
                stop_event.set()
                #M2_OFF = DVP_12SE.M2_ON(b':010508020000F0\r\n')
                M2_state = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
                print("M5 stop", M2_state)
                time.sleep(0.1)
                shutdown.set()
            time.sleep(2)
    except Exception as e:
        print("PLC thread error:", e)
    finally:
        # 一定要在這裡把 PSU 也關掉或觸發 shutdown
        shutdown.set()

def cycle_thread():
    """調度：充/放電结束後，休息→保存DAQ→EIS量測→休息→切下一模式"""
    global mode, df_101, df_102, df_111
    while not shutdown.is_set():
        try:
            finished = charge_or_discharge_flag.get(timeout=1)  # "charge" or "discharge"
        except:
            continue
        print(f"== {finished} 完成，休息 1min ==")
        try:
            # 關閉 PSU 輸出
            PDS20_36A.output(0)
            # 關閉電子負載
            Rigol_load.input(0)
            # 停止 DAQ 掃描
            DAQ_970a.scan_stop()
            print("已關閉 PSU、電子負載 及 DAQ")
        except Exception as e:
            print("停用裝置時發生錯誤：", e)
        time.sleep(60)  # 休息 10 min
        print("== 10min 休息结束，開始 EIS 量測 ==")
        LCR_EIS_sweep(
            LCR_ZM2371,
            start_freq  = -3,
            stop_freq   =  5,
            points     = 10,
        )
        print("== EIS 完成，休息 10min ==")
        time.sleep(60)
        if charge_cycle_count >= 1 and discharge_cycle_count >= 1:
            print("⚠️ 充電與放電各 3 次完成，系統停止。")
            shutdown.set()
            return
        if eis_shutdown_flag.is_set():
            print("⚠️ EIS 後確認：因容量衰減，系統停止。")
            shutdown.set()
            return
        with mode_lock:
            mode = "discharge" if finished=="charge" else "charge"
        print(f"== 切換到模式：{mode} ==")
        #DAQ_ON_event.set()
        
def charge_discharge_mode():
    global mode
    while not shutdown.is_set():
        with mode_lock:
            m = mode
        #mode = charge_or_discharge_flag.get()
        if m == "charge":
            volt, curr = PDS20_36A.output_Set(4.2, 5.2)
            print("PSU set")
            time.sleep(0.5)
            Y0_ON = DVP_12SE.M8_Y0_output(b':01050808FF00EB\r\n')
            Y0_state = DVP_12SE.Y0_state_read(b':010105000001F8\r\n')
            print("Y0 open")
            DAQ_ON_event.set()
            time.sleep(0.05)
            PSU_output = PDS20_36A.output(1)
            print("Charge: PSU ON, waiting for cutoff")
            charge_OR_discharge_finish_event.wait()
            print("Charge: cutoff detected, shutting down PSU")
            # 5) 關 PSU、開串放電繼電器 M2
            #PDS20_36A.output(0)
            charge_OR_discharge_finish_event.clear()
            charge_or_discharge_flag.put("charge")
            # 等待 cycle_thread 把 mode 切成 "discharge"
            old = m
            while True:
                with mode_lock:
                    if mode != old:
                        break
                time.sleep(0.1)
            """ with mode_lock:
                mode = "discharge" """
        elif m == "discharge":
            curr = Rigol_load.static_CC_mode_curr_set(5.2)
            print("E_load set")
            time.sleep(0.5)
            Y0_OFF = DVP_12SE.M8_Y0_output(b':010505000000F5\r\n')
            Y0_state = DVP_12SE.Y0_state_read(b':010105000001F8\r\n')
            print("Y0 close")
            DAQ_ON_event.set()
            time.sleep(0.05)
            E_load_input = Rigol_load.input(1)
            print("DIscharge: E_load ON, waiting for cutoff")
            charge_OR_discharge_finish_event.wait()
            print("Disharge: cutoff detected, shutting down E_load")
            # 5) 關 PSU、開串放電繼電器 M2
            #E_load_input = Rigol_load.input(0)
            charge_OR_discharge_finish_event.clear()
            charge_or_discharge_flag.put("discharge")
            old = m
            while True:
                with mode_lock:
                    if mode != old:
                        break
                time.sleep(0.1)
            """ with mode_lock:
                mode = "charge" """
        time.sleep(0.1)

def DAQ():
    global df_101, df_102, df_111, mode
    global charge_cycle_count, discharge_cycle_count, discharge_capacities, capacity_change, curr
    global latest_voltage, latest_current, latest_temperature, daq_active
    while not shutdown.is_set():
        DAQ_ON_event.wait()
        DAQ_ON_event.clear()
        if shutdown.is_set():
            break
        print("DAQ: start scanning")
        daq_active = True
        DAQ_970a.scan_start()
        time.sleep(0.05) # 等待掃描開始
        while not shutdown.is_set():
            with mode_lock:
                m = mode
            if m not in ("charge", "discharge"):
                # 如果模式被意外改走，就提前停止採集，等下個信號
                break
            if m in ("charge","discharge"):
                if DAQ_970a.data_point() != 0:
                    data = DAQ_970a.real_time_get_channel_data()
                    Data = DAQ_970a.split_read_data(data)
                    new_df_101, new_df_102, new_df_111 = DAQ_970a.get_channel_data(Data)
                    df_101 = pd.concat([df_101, new_df_101], ignore_index=True)
                    df_102 = pd.concat([df_102, new_df_102], ignore_index=True)
                    df_111 = pd.concat([df_111, new_df_111], ignore_index=True)
                    #print(df_101, df_102, df_111)
                    if len(df_101) >= 5 and len(df_102) >= 5 and len(df_111) >= 5:
                        voltage_average = df_101['Voltage'].rolling(window = 5).mean().round(4)
                        temperature_average = df_102['Temperature'].rolling(window = 5).mean().round(4)
                        current_average = df_111['Current'].rolling(window = 5).mean().round(4)
                        # Ensure you are accessing the most recent values
                        recent_voltage_avg = voltage_average.iloc[-1]
                        recent_temperature_avg = temperature_average.iloc[-1]
                        recent_current_avg = current_average.iloc[-1]
                        # 更新給 UI 顯示
                        latest_voltage     = recent_voltage_avg
                        latest_current     = recent_current_avg
                        latest_temperature = recent_temperature_avg
                        print(f"voltage:{recent_voltage_avg} current:{recent_current_avg} temperature:{recent_temperature_avg}")
                        #print(charge_or_discharge_flag.get())
                        with mode_lock:
                            m = mode
                        if (m == "charge" and ((charge_VOLtage_LOW <= recent_voltage_avg <= charge_VOLtage_HIGH) or recent_current_avg <= charge_CURRENT_THRESH)) \
                        or (m == "discharge" and (discharge_voltage_LOW <= recent_voltage_avg <= discharge_voltage_HIGH)):
                            if m == "charge":
                                #current_cycle = charge_cycle_count
                                PDS20_36A.output(0)# 關 PSU
                                time.sleep(0.2)
                                DVP_12SE.M8_Y0_output(b':010505000000F5\r\n')               # 關Y0(relay)
                                time.sleep(0.1)
                                DAQ_970a.scan_stop()
                                charge_cycle_count += 1
                                if charge_cycle_count >= 1 and discharge_cycle_count >= 1:
                                    print("⚠️ 充電與放電各 3 次完成，系統準備停止。")
                                break
                            else:
                                #current_cycle = discharge_cycle_count
                                Rigol_load.input(0)                                         # 關電子負載
                                time.sleep(0.2)
                                DVP_12SE.M8_Y0_output(b':01050808FF00EB\r\n')               # 開Y0(relay)
                                time.sleep(0.1)
                                DAQ_970a.scan_stop()
                                # --- 只有放電時才計算紀錄容量  ------------------
                                # 1) 計算放電時間（以小時為單位）
                                total_time = df_111['Timestamp'].iloc[-1] - df_111['Timestamp'].iloc[0]
                                # 2) 計算放電總容量 (Ah)
                                discharge_capacity = curr * (total_time.total_seconds() / 3600)
                                # 3) 把容量寫入 df_111
                                col = 'Capacity_Ah'
                                df_111[col] = None
                                df_111.iat[0, df_111.columns.get_loc(col)] = discharge_capacity
                                # 4) 追加到全局列表，並檢查是否低於首次放電容量的 80%
                                discharge_capacities.append(discharge_capacity)
                                if len(discharge_capacities) >= 2:
                                    first = discharge_capacities[0]
                                    latest = discharge_capacities[-1]
                                    capacity_change = latest / first * 100
                                    if capacity_change < 80:
                                        print("⚠️ 放電容量衰減超過20%，停止充放電循環！")
                                        PDS20_36A.output(0)
                                        Rigol_load.input(0)
                                        DAQ_970a.scan_stop()
                                        eis_shutdown_flag.set()
                                        break
                                discharge_cycle_count += 1
                                if charge_cycle_count >= 1 and discharge_cycle_count >= 1:
                                    print("⚠️ 充電與放電各 3 次完成，系統準備停止。")
                                break
        try:
            DAQ_970a.scan_stop()
        except Exception as e:
            print("掃描停止出錯:", e)
        finally:
            daq_active = False
        print(f">>> DAQ 檢測到 {m} 截止，已關 scanning")
        for df, path in [
            (df_101, f"channel_101_{m}"),
            (df_102, f"channel_102_{m}"),
            (df_111, f"channel_111_{m}"),
            ]:
            total_time = df['Timestamp'].iloc[-1] - df['Timestamp'].iloc[0]
            df['Elapsed'] = None
            df.at[0, 'Elapsed'] = total_time
            instrument.save_dataframe_to_csv_with_incremented_filename(
                df, f"C:/Users/zx511/battery_test_project/csv/{path}"
                )

            # 4) 清空DF，為下一次循環準備
        df_101 = make_empty_df(101, 'Voltage')
        df_102 = make_empty_df(102, 'Temperature')
        df_111 = make_empty_df(111, 'Current')
        charge_OR_discharge_finish_event.set()      # 通知模式結束做後續
                                
def LCR_EIS_sweep(lcr, start_freq, stop_freq, points):
    """
    lcr: 已初始化的 LCR 物件
    start_exp, stop_exp: 掃頻範圍的 10^start_exp 到 10^stop_exp
    points: 掃描點數
    csv_prefix: 存檔檔名前綴
    """
    global mode
    with mode_lock:
            m = mode
            if m == "charge":
                cycle = charge_cycle_count
            elif m == "discharge":
                cycle = discharge_cycle_count
    print("EIS 開始量測")
    freqs = LCR_ZM2371.freq_range(start_freq, stop_freq, points)
    results = []
    for freq in freqs:
        LCR_response_freq = LCR_ZM2371.measure_freq(freq)
        start_time = time.time()
        result = LCR_ZM2371.start_measure()
        end_time = time.time()
        duration = end_time - start_time
        results.append((LCR_response_freq, result))
        print(duration, result)
    # 解析成 DataFrame
    data = []
    for freq_str, value_str in results:
        f = float(freq_str.strip())
        parts = value_str.strip().split(',')
        real = float(parts[1])
        imag = float(parts[2])
        data.append((f, real, imag))
    df = pd.DataFrame(data, columns=["Frequency (Hz)", "Zreal", "Zimag"])
    base_path = r"C:\Users\zx511\battery_test_project\csv\EIS"
    os.makedirs(base_path, exist_ok=True)  # 如果資料夾不存在則自動建立
    filename = os.path.join(base_path, f"EIS_{m}_cycle_{cycle}.csv")
    df.to_csv(filename, index=False)
    print(f"EIS 資料已儲存至 {filename}")
# 在此假設您已將原本各個工作執行緒的函式（PLC_safe、cycle_thread、charge_discharge_mode、DAQ、LCR_EIS_sweep）
# 完整複製進來並且不動。下面只示範 UI 相關與程式啟動整合。

# --- Tkinter UI 部分 ---
def on_mode_change():
    with mode_lock:
        global mode
        mode = mode_var.get()

def start_process():
    start_btn.config(state='disabled')
    charge_rb.config(state='disabled')
    discharge_rb.config(state='disabled')
    emergency_btn.config(state='normal')
    # 啟動工作執行緒
    Thread(target=PLC_safe, daemon=True).start()
    Thread(target=cycle_thread, daemon=True).start()
    Thread(target=charge_discharge_mode, daemon=True).start()
    Thread(target=DAQ, daemon=True).start()
    update_status()     # 啟動 UI 週期更新

def emergency_stop():
    shutdown.set()

def update_status():
    # 1) RUNNING／STOPPED 狀態燈
    if shutdown.is_set():
        status_lbl.config(text="STOPPED", bg="red")
    else:
        status_lbl.config(text="RUNNING", bg="green")

    # 2) 目前模式
    with mode_lock:
        current = mode or "─"
    mode_display_lbl.config(text=f"目前模式：{current.capitalize()}")

    # 3) Charge／Discharge 次數
    charge_count_lbl.config(text=f"Charge 次數：{charge_cycle_count}")
    discharge_count_lbl.config(text=f"Discharge 次數：{discharge_cycle_count}")

    # 4) DAQ 三值更新
    vol_lbl.config(text=f"{latest_voltage:.3f} V")
    cur_lbl.config(text=f"{latest_current:.3f} A")
    temp_lbl.config(text=f"{latest_temperature:.2f} °C")

    # 5) DAQ 狀態指示燈
    daq_indicator.config(bg="green" if daq_active else "gray")

    # 每 200ms 再呼叫自己，只要還沒 shutdown
    if not shutdown.is_set():
        root.after(500, update_status)

# 建立主視窗
root = tk.Tk()
root.title("Battery Test 控制介面")

# 模式選擇
mode_var = tk.StringVar(value="charge")
mode_var.trace_add('write', lambda *args: on_mode_change())
charge_rb = tk.Radiobutton(root, text="Charge 模式", variable=mode_var, value="charge")
discharge_rb = tk.Radiobutton(root, text="Discharge 模式", variable=mode_var, value="discharge")
charge_rb.grid(row=0, column=0, padx=10, pady=5, sticky='w')
discharge_rb.grid(row=0, column=1, padx=10, pady=5, sticky='w')

# 開始與緊急停止按鈕
start_btn     = tk.Button(root, text="開始執行", command=start_process)
emergency_btn = tk.Button(root, text="緊急停止", command=emergency_stop, state='disabled')
start_btn.grid(row=1, column=0, padx=10, pady=10)
emergency_btn.grid(row=1, column=1, padx=10, pady=10)

# 狀態燈
status_lbl = tk.Label(root, text="READY", width=12, bg="gray", fg="white", font=('Arial', 12, 'bold'))
status_lbl.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

# 新增：目前 mode 顯示
mode_display_lbl = tk.Label(root, text="目前模式：─", font=('Arial', 10))
mode_display_lbl.grid(row=3, column=0, columnspan=2, padx=10, pady=2)

# 新增：Charge / Discharge 次數顯示
charge_count_lbl    = tk.Label(root, text="Charge 次數：0",    font=('Arial', 10))
discharge_count_lbl = tk.Label(root, text="Discharge 次數：0", font=('Arial', 10))
charge_count_lbl.grid(row=4, column=0, padx=10, pady=2, sticky='w')
discharge_count_lbl.grid(row=4, column=1, padx=10, pady=2, sticky='w')

# 顯示三個即時數值
tk.Label(root, text="Voltage:").grid(row=5, column=0, sticky='e', padx=5)
vol_lbl = tk.Label(root, text="0.000 V")
vol_lbl.grid(row=5, column=1, sticky='w')

tk.Label(root, text="Current:").grid(row=6, column=0, sticky='e', padx=5)
cur_lbl = tk.Label(root, text="0.000 A")
cur_lbl.grid(row=6, column=1, sticky='w')

tk.Label(root, text="Temp:").grid(row=7, column=0, sticky='e', padx=5)
temp_lbl = tk.Label(root, text="0.00 °C")
temp_lbl.grid(row=7, column=1, sticky='w')

# DAQ 狀態指示燈
daq_indicator = tk.Label(root, text="DAQ", width=8, bg="gray", fg="white", font=('Arial', 10, 'bold'))
daq_indicator.grid(row=8, column=0, columnspan=2, pady=5)

# 視窗關閉時也觸發 shutdown
def on_closing():
    shutdown.set()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# 啟動 Tkinter 事件迴圈
root.mainloop()
