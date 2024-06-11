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
cell_Ah = 0.01
charge_CC_cutoff_voltage_upper = 9
charge_CC_cutoff_voltage_lower = 10.005
charge_CC_current_upper = cell_Ah 
charge_CC_current_lower = cell_Ah - 0.003
charge_CV_cutoff_current = 0.004
column_name = "Total_time"
DVP_12SE = instrument.DVP_PLC('COM3', '12SE')
time.sleep(1) #要確保rs232命令被發出
M1183_state = DVP_12SE.M1183_output(b':01050C9F00004F\r\n')
output_state = DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
time.sleep(1)

DAQ_970a = instrument.DAQ("USB0::0x2A8D::0x5101::MY58017225::INSTR", "970a")
DAQ_970a.channel_function("VOLT:DC", 10, 101)
DAQ_970a.channel_function("VOLT:DC", "100mV", 111)
DAQ_970a.channel_scan_config("(@101, 111)", 1, 0.035)
time.sleep(1)


PDS20_36A = instrument.power_supply("ASRL5::INSTR", "PDS20")
volt, curr = PDS20_36A.output_Set(8.4, 2)

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
        print(df_101)
        #print(f"voltage:{df_101['Voltage'].iloc[-1]}, current:{df_111['Current'].iloc[-1]}")
        """
        if volt == 10 and 9 <= df_101['Voltage'].iloc[-1] <= 10 and 0.008 <= df_111['Current'].iloc[-1] <= 0.009:
            volt, curr = PDS20_36A.output_Set(4.2, 0.01)
            print("CV mode")
        """
        if volt == 8.4 and 8.37 <= df_101['Voltage'].iloc[-1] <= 8.4:
            PSU_output = PDS20_36A.output(0)
            time.sleep(1)
            DAQ_970a.scan_stop()
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
print(df_101)
print(df_111)
instrument.save_dataframe_to_csv_with_incremented_filename(df_101, "C:/Users/zx511/hello/csv/channel_101_charge")
instrument.save_dataframe_to_csv_with_incremented_filename(df_111, "C:/Users/zx511/hello/csv/channel_111_charge")
#save_dataframe_to_csv_with_incremented_filename(PLC_voltage, "C:/Users/zx511/hello/csv/PLC_data")

