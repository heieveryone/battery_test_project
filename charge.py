import pyvisa
import time
import threading
import pandas as pd
import instrument
"""
rm = pyvisa.ResourceManager()
print(rm.list_resources()) #列出可用資源
print(rm) #輸出Visa庫在電腦的位置
"""
cell_Ah = 5.2
charge_CC_cutoff_voltage_upper = 9
charge_CC_cutoff_voltage_lower = 10.005
charge_CC_current_upper = cell_Ah 
charge_CC_current_lower = cell_Ah - 0.003
charge_CV_cutoff_current = 0.004
column_name = "Total_time"
DVP_12SE = instrument.DVP_PLC('COM4', '12SE')
time.sleep(1) #要確保rs232命令被發出
M1183_state = DVP_12SE.M1183_output(b':01050C9F00004F\r\n')
output_state = DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
time.sleep(1)

DAQ_970a = instrument.DAQ("USB0::0x2A8D::0x5101::MY58017225::INSTR", "970a")
DAQ_970a.channel_function("VOLT:DC", 10, 101)
DAQ_970a.channel_function("VOLT:DC", "100mV", 111)
DAQ_970a.channel_scan_config("(@101, 111)", 1, 0.035)
time.sleep(1)


PDS20_36A = instrument.power_supply("ASRL3::INSTR", "PDS20")
volt, curr = PDS20_36A.output_Set(4.2, 5.2)

time.sleep(5)

df_101 = pd.DataFrame(columns=['Channel', 'Timestamp', 'Voltage', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'])
df_111 = pd.DataFrame(columns=['Channel', 'Timestamp', 'Current', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'])
if M1183_state == str(b':01050C9F00004F\r\n') and output_state == str(b':01050500FF00F6\r\n'):
    print(DAQ_970a.scan_start())
    PSU_output = PDS20_36A.output(1)
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
        if len(df_101) >= 5 and len(df_111) >= 5:
            voltage_average = df_101['Voltage'].rolling(window = 5).mean().round(4)
            current_average = df_111['Current'].rolling(window = 5).mean().round(4)
            # Ensure you are accessing the most recent values
            recent_voltage_avg = voltage_average.iloc[-1]
            recent_current_avg = current_average.iloc[-1]
            print(recent_current_avg, recent_voltage_avg)
            if (4.195 <= recent_voltage_avg <= 4.203) & (recent_current_avg <= 0.052):
                DAQ_970a.scan_stop()
                time.sleep(0.05)
                print("PSU OFF")
                PSU_output = PDS20_36A.output(0)
                print("cut off voltage") 
                break
        
elif M1183_state != str(b':01050C9F00004F\r\n') or output_state != str(b':01050500FF00F6\r\n'):
    print("fail to turn on")
        
time.sleep(2)
#PSU_output = PDS20_36A.output(0)
time.sleep(2)
output_state = DVP_12SE.Y0_output(b':010505000000F5\r\n')

if PSU_output == 0 and output_state == str(b':010505000000F5\r\n'):
    print("Finish charge")
total_time_elapsed = df_101['Timestamp'].iloc[-1] - df_101['Timestamp'].iloc[0]
df_101[column_name] = None
df_101.iat[0, df_101.columns.get_loc(column_name)] = total_time_elapsed
total_time_elapsed = df_111['Timestamp'].iloc[-1] - df_111['Timestamp'].iloc[0]
df_111[column_name] = None
df_111.iat[0, df_111.columns.get_loc(column_name)] = total_time_elapsed
"""
# 計算相鄰電壓和電流的差
delta_voltage = df_101['Voltage'].diff()
delta_current = df_111['Current'].diff()
# 計算電阻值
resistance = delta_voltage / delta_current
df_resistance = pd.DataFrame({
    'Timestamp': df_101['Timestamp'],
    'Voltage': df_101['Voltage'],
    'Current': df_111['Current'],
    'Resistance': resistance
})
"""
print(df_101)
print(df_111)
instrument.save_dataframe_to_csv_with_incremented_filename(df_101, "C:/Users/Acer/battery_test_project/csv/channel_101_charge")
instrument.save_dataframe_to_csv_with_incremented_filename(df_111, "C:/Users/Acer/battery_test_project/csv/channel_111_charge")
#instrument.save_dataframe_to_csv_with_incremented_filename(df_resistance, "C:/Users/Acer/battery_test_project/csv/charge_resistance")
#save_dataframe_to_csv_with_incremented_filename(PLC_voltage, "C:/Users/zx511/hello/csv/PLC_data")

