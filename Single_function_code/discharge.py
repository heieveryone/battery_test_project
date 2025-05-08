import time
import pandas as pd
import instrument

cell_mAh = None
discharge_cutoff_voltage_lower = 2.995
discharge_cutoff_voltage_upper = 3.005
column_name_Capacity = "Capacity"
column_name = "Total_time"
Rigol_load = instrument.dc_electronic_load('USB0::0x1AB1::0x0E11::DL3A260500107::INSTR', 'DL3021')
Rigol_load.static_function('CURR')
range = Rigol_load.static_CC_mode_curr_range(40)
curr = Rigol_load.static_CC_mode_curr_set(18.2)
time.sleep(1)

DVP_12SE = instrument.DVP_PLC('COM4', '12SE')
time.sleep(1) #要確保rs232命令被發出
M1183_state = DVP_12SE.M1183_output(b':01050C9F00004F\r\n')
output_state = DVP_12SE.Y0_output(b':010505000000F5\r\n')
print(M1183_state, output_state)
time.sleep(1)

DAQ_970a = instrument.DAQ("USB0::0x2A8D::0x5101::MY58017225::0::INSTR", "970a")
DAQ_970a.channel_function("VOLT:DC", 10, 101)
DAQ_970a.channel_function("TEMP:TCouple", 'J', 102)
DAQ_970a.channel_function("VOLT:DC", "100mV", 111)
DAQ_970a.channel_scan_config("(@101, 102, 111)", 1, 0.035)
time.sleep(1)
df_101 = pd.DataFrame(columns=['Channel', 'Timestamp', 'Voltage', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'])
df_102 = pd.DataFrame(columns=['Channel', 'Timestamp', 'Temperature', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'])
df_111 = pd.DataFrame(columns=['Channel', 'Timestamp', 'Current', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'])
time.sleep(5)


if M1183_state == str(b':01050C9F00004F\r\n') and output_state == str(b':010505000000F5\r\n'):
    print(DAQ_970a.scan_start())
    E_load_input = Rigol_load.input(1)
    while 1:
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
                if 3.59 <= recent_voltage_avg < 3.601:
                    DAQ_970a.scan_stop()
                    time.sleep(0.05)
                    E_load_input = Rigol_load.input(0)
                    print("cut off voltage")
                    break
elif M1183_state != str(b':01050C9F00004F\r\n') or output_state != str(b':010505000000F5\r\n'):
    print("fail to turn on")

time.sleep(2)
if E_load_input == 0 and output_state == str(b':010505000000F5\r\n'):
    print("Finish discharge")
# 計算每個 Timestamp 與第一個 Timestamp 的時間差（以小時為單位）
total_hours = (df_111['Timestamp'].iloc[-1] - df_111['Timestamp'].iloc[0]).total_seconds() / 3600
discharge_Capacity = curr * total_hours
"""
# 計算相鄰電壓和電流的差
delta_voltage = df_101['Voltage'].diff().iloc[1:]
delta_current = df_111['Current'].diff().iloc[1:]
# 計算電阻值
resistance = delta_voltage / delta_current
df_resistance = pd.DataFrame({
    'Timestamp': df_101['Timestamp'],
    'Voltage': df_101['Voltage'],
    'Current': df_111['Current'],
    'Resistance': resistance
})
"""
total_time_elapsed = df_101['Timestamp'].iloc[-1] - df_101['Timestamp'].iloc[0]
df_101[column_name] = None
df_101.iat[0, df_101.columns.get_loc(column_name)] = total_time_elapsed
total_time_elapsed = df_102['Timestamp'].iloc[-1] - df_102['Timestamp'].iloc[0]
df_102[column_name] = None
df_102.iat[0, df_102.columns.get_loc(column_name)] = total_time_elapsed
total_time_elapsed = df_111['Timestamp'].iloc[-1] - df_111['Timestamp'].iloc[0]
df_111[column_name] = None
df_111.iat[0, df_111.columns.get_loc(column_name)] = total_time_elapsed
df_111[column_name_Capacity] = None
df_111.iat[0, df_111.columns.get_loc(column_name_Capacity)] = discharge_Capacity
#print(df_101)
#print(df_111)

instrument.save_dataframe_to_csv_with_incremented_filename(df_101, "C:/Users/Acer/battery_test_project/csv/channel_101_discharge")
instrument.save_dataframe_to_csv_with_incremented_filename(df_102, "C:/Users/Acer/battery_test_project/csv/channel_102_discharge")
instrument.save_dataframe_to_csv_with_incremented_filename(df_111, "C:/Users/Acer/battery_test_project/csv/channel_111_discharge")
#instrument.save_dataframe_to_csv_with_incremented_filename(df_resistance, "C:/Users/Acer/battery_test_project/csv/discharge_resistance")

instrument.rm.close()