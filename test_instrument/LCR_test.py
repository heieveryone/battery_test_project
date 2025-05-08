import pyvisa
import time
import instrument
import pandas as pd
LCR_ZM2371 = instrument.LCR("USB0::0x0D4A::0x0016::9429358::INSTR", "ZM2371")
LCR_ZM2371.timeout()
LCR_ZM2371.measure_config("OFF", "BUS", "ON", "LONG", "OFF")
LCR_ZM2371.measure_parameter("REAL", "IMAG")
LCR_ZM2371.measure_source("VOLT", 0.01, 0)
freqs = LCR_ZM2371.freq_range(-2, 5, 10)
results = []
print("start measure")

for freq in freqs:
    LCR_response_freq = LCR_ZM2371.measure_freq(freq)
    start_time = time.time()
    result = LCR_ZM2371.start_measure()
    end_time = time.time()
    duration = end_time - start_time
    results.append((LCR_response_freq, result))
    print(duration, result)

print(results)
LCR_ZM2371.close()
data = []
for freq_str, value_str in results:
    freq = float(freq_str.strip())
    parts = value_str.strip().split(',')
    real = float(parts[1])
    imag = float(parts[2])
    data.append((freq_str, real, imag))
    
df = pd.DataFrame(data, columns=["Frequency (Hz)", "Zreal", "Zimag"])
csv_path = "test_EIS1.csv"
df.to_csv(csv_path, index=False)
