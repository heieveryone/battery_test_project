import time
import pandas as pd
import instrument
import threading
from queue import Queue
import os

DVP_12SE = instrument.DVP_PLC('COM3', '12SE')
time.sleep(0.5) #要確保rs232命令被發出
PDS20_36A = instrument.power_supply("ASRL16::INSTR", "PDS20")
time.sleep(0.5)
Rigol_load = instrument.dc_electronic_load('USB0::0x1AB1::0x0E11::DL3A260500107::INSTR', 'DL3021')
Rigol_load.static_function('CURR')
range = Rigol_load.static_CC_mode_curr_range(40)
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

DAQ_Start_event = threading.Event() #觸發DAQ紀錄充放電
PSU_off_event = threading.Event() #PSU關觸發Y0切換
stop_event = threading.Event() #M3,M5停止PSU觸發
shutdown = threading.Event() #把所有程式關掉
DAQ_ON_event = threading.Event() #將DAQ打開訊號當成PSU觸發
charge_OR_discharge_finish_event = threading.Event() #充放電結束觸發
eis_shutdown_flag = threading.Event() #EIS結束觸發
M3_M5_trigger = Queue() #把M3,M5觸發信號放到Queue中
charge_or_discharge_flag = Queue() #把目前要充電或放電的旗標放到Queue中
mode_lock = threading.Lock()
mode = None
mode = input("charge or discharge: ").strip().lower()
print("啟動模式：", mode)

target_Y0_ON = str(b':01010101FC\r\n')
target_Y0_OFF = str(b':01010100FD\r\n')
target_M2_ON = str(b':01010103FA\r\n')
target_M2_OFF = str(b':01010102FB\r\n')
target_M3_ON = str(b':01010103FA\r\n')
target_M3_OFF = str(b':01010102FB\r\n')
target_M5_ON = str(b':01010105F8\r\n')
target_M5_OFF = str(b':01010104F9\r\n')

df_101 = pd.DataFrame(columns=['Channel', 'Timestamp', 'Voltage', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'])
df_102 = pd.DataFrame(columns=['Channel', 'Timestamp', 'Temperature', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'])
df_111 = pd.DataFrame(columns=['Channel', 'Timestamp', 'Current', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'])
discharge_capacities = [] # 用來存放放電容量的列表
# —— 充電停止門檻常數 —— #
charge_VOLtage_LOW, charge_VOLtage_HIGH = 4.15, 4.16
charge_CURRENT_THRESH = 0.052
# —— 放電停止門檻常數 —— #
discharge_voltage_LOW, discharge_voltage_HIGH = 3.9, 3.91
# —— 充放電循環計數器 —— #
charge_cycle_count = 0
discharge_cycle_count = 0
# 三組 DataFrame清空，為存放後續的資料做準備
def make_empty_df(channel, name):
    cols = ['Channel','Timestamp'] + ([name] if name=='Temperature' else [ {101:'Voltage',111:'Current'}[channel] ]) + ['Year','Month','Day','Hour','Minute','Second']
    return pd.DataFrame(columns=cols)

df_101 = make_empty_df(101, 'Voltage')
df_102 = make_empty_df(102, 'Temperature')
df_111 = make_empty_df(111, 'Current')

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
        print(f"== {finished} 完成，休息 10min ==")
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
        time.sleep(600)  # 休息 10 min
        print("== 10min 休息结束，開始 EIS 量測 ==")
        LCR_EIS_sweep(
            LCR_ZM2371,
            start_freq  = -3,
            stop_freq   =  5,
            points     = 10,
        )
        print("== EIS 完成，休息 10min ==")
        time.sleep(600)
        if charge_cycle_count >= 1 and discharge_cycle_count >= 1:
            print("⚠️ 充電與放電各 1 次完成，系統停止。")
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
    global charge_cycle_count, discharge_cycle_count, discharge_capacities, curr, capacity_change
    while not shutdown.is_set():
        DAQ_ON_event.wait()
        DAQ_ON_event.clear()
        if shutdown.is_set():
            break
        print("DAQ: start scanning")
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
                        print(f"voltage:{recent_voltage_avg} current:{recent_current_avg} temperature:{recent_temperature_avg}")
                        #print(charge_or_discharge_flag.get())
                        with mode_lock:
                            m = mode
                        if (m == "charge" and ((charge_VOLtage_LOW <= recent_voltage_avg <= charge_VOLtage_HIGH) and recent_current_avg <= charge_CURRENT_THRESH)) \
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

if __name__ == "__main__":
    # 啟動 PLC 監控執行緒
    threading.Thread(target=PLC_safe, daemon=True).start()
    # 啟動充放電循環執行緒
    threading.Thread(target=cycle_thread, daemon=True).start()
    # 啟動充放電控制執行緒
    threading.Thread(target=charge_discharge_mode, daemon=True).start()
    # 啟動 DAQ 執行緒
    threading.Thread(target=DAQ, daemon=True).start()
    
    # 主執行緒只要等 Ctrl-C 設定 shutdown
    try:
        while not shutdown.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        PDS20_36A.output(0)
        Rigol_load.input(0)
        DAQ_970a.scan_stop()
        LCR_ZM2371.close()
        shutdown.set()
    finally:
        # 在這裡印出總次數
        print("=== 程式結束 ===")
        print(f"總共執行充電 {charge_cycle_count} 次")
        print(f"總共執行放電 {discharge_cycle_count} 次")
        print("每次放電容量：", discharge_capacities)