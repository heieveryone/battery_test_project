import pyvisa
import time
import threading
import pandas as pd
import instrument

cell_mAh = None
discharge_cutoff_voltage_lower = 2.995
discharge_cutoff_voltage_upper = 3.005
column_name_Time = "Total_time"
column_name_Capacity = "Capacity"

Rigol_load = instrument.dc_electronic_load('USB0::0x1AB1::0x0E11::DL3A260500107::INSTR', 'DL3021')
Rigol_load.static_function('CURR')
curr = Rigol_load.static_CC_mode_curr_set(2)
time.sleep(1)

DVP_12SE = instrument.DVP_PLC('COM3', '12SE')
time.sleep(1) #要確保rs232命令被發出
M1183_state = DVP_12SE.M1183_output(b':01050C9F00004F\r\n')
output_state = DVP_12SE.Y0_output(b':010505000000F5\r\n')
time.sleep(1)

DAQ_970a = instrument.DAQ("USB0::0x2A8D::0x5101::MY58017225::0::INSTR", "970a")
DAQ_970a.channel_function("VOLT:DC", 10, 101)
DAQ_970a.channel_function("VOLT:DC", "100mV", 111)
DAQ_970a.channel_scan_config("(@101, 111)", 1, 0.035)
time.sleep(1)
df_101 = pd.DataFrame(columns=['Channel', 'Timestamp', 'Voltage', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'])
df_111 = pd.DataFrame(columns=['Channel', 'Timestamp', 'Current', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'])
time.sleep(5)


if M1183_state == str(b':01050C9F00004F\r\n') and output_state == str(b':010505000000F5\r\n'):
    print(DAQ_970a.scan_start())
    E_load_input = Rigol_load.input(1)
    while 1:
        time.sleep(0.5)
        data = DAQ_970a.real_time_get_channel_data()
        Data = DAQ_970a.spilt_read_data(data)
        new_df_101, new_df_111 = DAQ_970a.get_channel_data(Data)
        #voltage = new_df_101['Voltage']
        #print(voltage, type(voltage))
        #current = new_df_111['Current']
        #print(new_df_101, type(new_df_101))
        df_101 = pd.concat([df_101, new_df_101], ignore_index=True)
        df_111 = pd.concat([df_111, new_df_111], ignore_index=True)
        print(df_101)
        #print(df_101)
        if 7.7 <= df_101['Voltage'].iloc[-1] < 7.79:
            E_load_input = Rigol_load.input(0)
            print("cut off voltage")
            time.sleep(0.1)
            DAQ_970a.scan_stop()
            break
elif M1183_state != str(b':01050C9F00004F\r\n') or output_state != str(b':010505000000F5\r\n'):
    print("fail to turn on")

time.sleep(2)
if E_load_input == 0 and output_state == str(b':010505000000F5\r\n'):
    print("Finish discharge")
#df_111['Current'] = df_111['Current'].apply(lambda x: abs(x))
#總花費時間，顯示為秒數或小時?
total_time_elapsed = df_111['Timestamp'].iloc[-1] - df_111['Timestamp'].iloc[0]
# 計算每個 Timestamp 與第一個 Timestamp 的時間差（以小時為單位）
total_hours = (df_111['Timestamp'].iloc[-1] - df_111['Timestamp'].iloc[0]).total_seconds() / 3600
discharge_Capacity = curr * total_hours
df_111[column_name_Time] = None
df_111.iat[0, df_111.columns.get_loc(column_name_Time)] = total_time_elapsed
df_111[column_name_Capacity] = None
df_111.iat[0, df_111.columns.get_loc(column_name_Capacity)] = discharge_Capacity
print(df_101)
print(df_111)
#df_111['discharge_Capacity'] = discharge_Capacity
instrument.save_dataframe_to_csv_with_incremented_filename(df_101, "C:/Users/zx511/hello/csv/channel_101_discharge")
instrument.save_dataframe_to_csv_with_incremented_filename(df_111, "C:/Users/zx511/hello/csv/channel_111_discharge")