#USB0::0x0D4A::0x0016::9429358::INSTR
import pyvisa
import numpy as np
import pandas as pd

def main():
    try:
        # 建立 VISA 資源管理器
        rm = pyvisa.ResourceManager()

        # USB 裝置字串（需確認實際序號與 VID/PID）
        usb_resource = "USB0::0x0D4A::0x0016::9429358::INSTR"
        session = rm.open_resource(usb_resource)

        # 設定逾時時間為 60 秒
        session.timeout = 60000
        session.write("*CLS")
        # 查詢儀器 ID
        idn = session.query("*IDN?")
        print(f"IDN: {idn}")
        model_name = idn.split(",")[1]
        serial_number = idn.split(",")[2]
        print(model_name)
        print(serial_number)
        # 重置儀器
        session.write("*RST")
        
        # 啟用連續觸發模式
        session.write(":INIT:CONT ON")
        session.write(":SENSe:FUNCtion:CONCurrent ON")
        #設定量測參數
        session.write(":CALC1:FORM REAL")
        session.write(":CALC2:FORM IMAG")
        # 設定參數：1kHz, 1V, LONG 測量時間,CV,average
        session.write(":SOUR:VOLT 10M")   # 設定電壓 1V
        session.write(":APER LONG")       # 設定平均模式為 LONG
        session.write(":RANG:AUTO ON")    #自動調整量測範圍
        session.write(":SOUR:VOLT:ALC ON")#CV mode
        #session.write(":AVER ON")         #平均數據
        #session.write(":AVER:COUN 3")     #平均多少筆
        #session.write(":SOUR:VOLT:OFFS 2")#DC offset
        
        #session.write(":DATA:FEED:CONT BUF1,NEV")
        """
        session.write(":DATA:POIN BUF1,10")
        session.write(':DATA:FEED BUF1,"CALC1","CALC2"')
        """
        freq_list = [1000, 2000]
        results = []
        frequencies = np.logspace(-1, 3, num=10)  # log10(0.001) = -3, log10(100000) = 5

        # 將每個頻率格式化為「最多 5 位有效數字」，符合儀器解析度要求
        formatted_frequencies = ["{:.5g}".format(f) for f in frequencies]

        # 顯示前後幾個檢查
        preview_freqs = formatted_frequencies[:5] + ["..."] + formatted_frequencies[-5:]

        print(preview_freqs)
        # 使用 BUS 模式觸發一次並讀取資料
        session.write(":TRIG:SOUR BUS")   # 設定觸發來源為 BUS
        for set_freq in frequencies:
            session.write(f":SOUR:FREQ {set_freq}")  # 設定頻率 1kHz
            session.write(":SOUR:FREQ?")
            freq = session.read()
            session.write("*TRG")             # 發送觸發指令
            result = session.read()   # 讀取資料
            results.append((freq, result))
            
        #data = session.query(":DATA? BUF1")         # 讀取結果
        print(f"測量結果: {results}")
    except Exception as e:
        print(session.write(":SYST:ERR?"))
    data = []
    for freq_str, value_str in results:
        freq = float(freq_str.strip())
        parts = value_str.strip().split(',')
        real = float(parts[1])
        imag = float(parts[2])
        data.append((freq, real, imag))
    print(data)
    df = pd.DataFrame(data, columns=["Frequency (Hz)", "Zreal", "Zimag"])
    csv_path = "test_EIS.csv"
    df.to_csv(csv_path, index=False)
if __name__ == "__main__":
    main()