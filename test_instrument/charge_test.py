import time
import pandas as pd
import instrument
import threading
from queue import Queue
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

DVP_12SE = instrument.DVP_PLC('COM3', '12SE')
time.sleep(0.5) #要確保rs232命令被發出
PDS20_36A = instrument.power_supply("ASRL16::INSTR", "PDS20")
time.sleep(0.5)
DAQ_970a = instrument.DAQ("USB0::0x2A8D::0x5101::MY58017225::INSTR", "970a")
DAQ_970a.channel_function("VOLT:DC", 10, 101)
DAQ_970a.channel_function("TEMP:TCouple", 'J', 102)
DAQ_970a.channel_function("VOLT:DC", "100mV", 111)
DAQ_970a.channel_scan_config("(@101, 102, 111)", 1, 0.035)
time.sleep(0.5)

y0_ON_event = threading.Event() #y0開觸發DAQ紀錄充放電
PSU_off_event = threading.Event() #PSU關觸發Y0切換
stop_event = threading.Event() #M3,M5停止PSU觸發
shutdown = threading.Event() #把所有程式關掉
DAQ_ON_event = threading.Event() #將DAQ打開訊號當成PSU觸發
charge_finish_event = threading.Event()
M3_M5_trigger = Queue() #把M3,M5觸發信號放到Queue中
charge_or_discharge_flag = Queue() #把目前要充電或放電的旗標放到Queue中


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

# —— 充電停止門檻常數 —— #
charge_VOLtage_LOW, charge_VOLtage_HIGH = 3.93, 3.94
charge_CURRENT_THRESH = 0.052
# —— 放電停止門檻常數 —— #
discharge_voltage_LOW, discharge_voltage_HIGH = 3.59, 3.601
charge_or_discharge_flag.put(input("charge or discharge:"))
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
                print("charge and under voltage")
                M3_M5_trigger.put("M3")
                stop_event.set()
                #M2_OFF = DVP_12SE.M2_ON(b':010508020000F0\r\n')
                M2_state = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
                print("M3 stop", M2_state)
                time.sleep(0.1)
            
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
            time.sleep(0.5)
    except Exception as e:
        print("PLC thread error:", e)
    finally:
        # 一定要在這裡把 PSU 也關掉或觸發 shutdown
        shutdown.set()
def charge():
    while not shutdown.is_set():
        if charge_or_discharge_flag.get() == "charge":
            volt, curr = PDS20_36A.output_Set(4.2, 4)
            print("PSU set")
            time.sleep(0.5)
            Y0_ON = DVP_12SE.M8_Y0_output(b':01050808FF00EB\r\n')
            Y0_state = DVP_12SE.Y0_state_read(b':010105000001F8\r\n')
            print("Y0 open")
            try:
                if Y0_state == target_Y0_ON:
                    print(DAQ_970a.scan_start())
                    time.sleep(2)
                    PSU_output = PDS20_36A.output(1)
                    while not charge_finish_event.is_set():
                        DAQ_test()
                        time.sleep(0.05)
                    charge_finish_event.clear()
                """             
                if stop_event.wait(timeout=0.5):
                    M3_or_M5 = M3_M5_trigger.get()
                    if M3_or_M5 == 'M3':
                        PSU_output = PDS20_36A.output(0)
                        
                        print('M3 close PSU')
                    else:
                        PSU_output = PDS20_36A.output(0)
                        print('M5 close PSU')
                    stop_event.clear()
                    if PSU_output == 0:
                        print("PSU off")
                            #Y0_OFF = DVP_12SE.M8_Y0_output(b':010505000000F5\r\n')
                """    
            except Exception as e:
                print("PSU thread error:", e)
            finally:
                # 5. 無論如何都要關 PSU、關 Y0，保證硬體安全
                PDS20_36A.output(0)
                DAQ_970a.scan_stop()
                #DVP_12SE.M8_Y0_output(b':010505000000F5\r\n')
                print("PSU and Y0 both off, thread exiting")
                #shutdown.set()
        time.sleep(10)
        LCR()
def E_Load():
    if charge_or_discharge_flag.get() == "discharge":
        try:
            print("switch to discharge")
        except Exception as e:
            print("Load thread error:", e)
        finally:
            print("finish")
def DAQ_test():
    global df_101, df_102, df_111
    try:
        if DAQ_970a.data_point() == 0:
            print("no new data")
            return
        if DAQ_970a.data_point() != 0:
            data = DAQ_970a.real_time_get_channel_data()
            Data = DAQ_970a.split_read_data(data)
            new_df_101, new_df_102, new_df_111 = DAQ_970a.get_channel_data(Data)
            df_101 = pd.concat([df_101, new_df_101], ignore_index=True)
            df_102 = pd.concat([df_102, new_df_102], ignore_index=True)
            df_111 = pd.concat([df_111, new_df_111], ignore_index=True)
            if len(df_101) >= 5 and len(df_102) >= 5 and len(df_111) >= 5:
                voltage_average = df_101['Voltage'].rolling(window = 5).mean().round(4)
                temperature_average = df_102['Temperature'].rolling(window = 5).mean().round(4)
                current_average = df_111['Current'].rolling(window = 5).mean().round(4)
                # Ensure you are accessing the most recent values
                recent_voltage_avg = voltage_average.iloc[-1]
                recent_temperature_avg = temperature_average.iloc[-1]
                recent_current_avg = current_average.iloc[-1]
                print(f"voltage:{recent_voltage_avg} current:{recent_current_avg} temperature:{recent_temperature_avg}")
                if charge_or_discharge_flag.get() == "charge":
                    if (charge_VOLtage_LOW <= recent_voltage_avg <= charge_VOLtage_HIGH) or (recent_current_avg <= charge_CURRENT_THRESH):
                        #DAQ_970a.scan_stop()
                        time.sleep(0.05)
                        PSU_output = PDS20_36A.output(0)
                        print(">>> DAQ 檢測到截止，PSU OFF")
                        time.sleep(0.05)
                        charge_finish_event.set()      # 通知 PSU thread 做後續
                        charge_or_discharge_flag.put("discharge")
                if charge_or_discharge_flag.get() == "discharge":
                    if (discharge_voltage_LOW <= recent_voltage_avg <= discharge_voltage_HIGH):
                        #DAQ_970a.scan_stop()
                        time.sleep(0.05)
                        #PSU_output = PDS20_36A.output(0)
                        print(">>> DAQ 檢測到截止，Load OFF")
                        #stop_event.set()      # 通知 PSU thread 做後續
                        charge_or_discharge_flag.put("charge")
    except Exception as e:
        print("DAQ thread error:", e)
        shutdown.set()
"""     finally:
        # 無論如何都得關 scan、關 shutdown
        try:
            DAQ_970a.scan_stop()
        except: pass
        print("DAQ thread exiting → shutdown") """

def LCR():
    try:
        print("switch to LCR")
        time.sleep(10)
    except Exception as e:
        print("Load thread error:", e)
    finally:
        print("finish")
"""
def cycle():
    while not shutdown.is_set():
        PSU()
        DAQ()
        charge_finish_event.wait()
        print("finish charge")
        time.sleep(10)
        LCR()
"""
if __name__ == "__main__":
    # 建立並啟動兩個 daemon 執行緒
    plc_t = threading.Thread(target=PLC_safe, daemon=True)
    charge_t = threading.Thread(target=charge, daemon=True)
    plc_t.start()
    charge_t.start()

    # 主線程只要阻塞，等 Ctrl-C 叫醒就 set(shutdown)
    try:
        while not shutdown.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught — shutting down")
        shutdown.set()

    # 等其它執行緒跑到 finally，然後結束程式
    plc_t.join(timeout=1)
    charge_t.join(timeout=1)
    print("All threads exited, program done.")
