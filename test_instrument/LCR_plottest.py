import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np

# 讀取 CSV 檔，請將 "data.csv" 改成你的檔案路徑
df = pd.read_csv("C:/Users/zx511/battery_test_project/test_EIS.csv")
# 計算阻抗大小與相位
df["Zmag"] = np.sqrt(df["Zreal"]**2 + df["Zimag"]**2)
df["Zphase"] = np.degrees(np.arctan2(df["Zimag"], df["Zreal"]))
# 假設 CSV 欄位分別為：量測頻率、實部阻抗、虛部阻抗
# 常用 Nyquist 圖繪製方式：x 軸為實部阻抗，y 軸為 - 虛部阻抗
fig = plt.figure(figsize=(14, 6))
gs = GridSpec(2, 2, width_ratios=[1.2, 2.2])  # 左邊小、右邊大
ax0 = fig.add_subplot(gs[:, 0])
ax0.plot(df["Zreal"], -df["Zimag"], marker='o', linestyle='-', color='b')
ax0.set_xlabel("Real Impedance (Ω)")
ax0.set_ylabel("-Imaginary Impedance (Ω)")
ax0.set_title("Nyquist Plot")
ax0.grid(True)
ax0.axis("equal")  # 保持 x、y 軸比例一致
# 找到最低頻（1 mHz）與最高頻（100 kHz）的資料點
min_freq_row = df.iloc[0]
max_freq_row = df.iloc[-1]

# 如果你確定第一筆是 1mHz，最後一筆是 100kHz，可以這樣標示：
ax0.annotate("1 mHz", 
             xy=(min_freq_row["Zreal"], -min_freq_row["Zimag"]),
             xytext=(min_freq_row["Zreal"]*1.1, -min_freq_row["Zimag"]*1.1),
             arrowprops=dict(facecolor='black', arrowstyle="->"),
             fontsize=10)

ax0.annotate("100 kHz", 
             xy=(max_freq_row["Zreal"], -max_freq_row["Zimag"]),
             xytext=(max_freq_row["Zreal"] * 500, -max_freq_row["Zimag"] * 500),
             arrowprops=dict(facecolor='black', arrowstyle="->"),
             fontsize=10)

ax1 = fig.add_subplot(gs[0, 1])
ax1.semilogx(df["Frequency (Hz)"], 20 * np.log10(df["Zmag"]))
ax1.set_ylabel("Magnitude (dB)")
ax1.grid(True, which='both', linestyle='--')
ax1.set_title("Bode plot")
# Phase plot
ax2 = fig.add_subplot(gs[1, 1])
ax2.semilogx(df["Frequency (Hz)"], df["Zphase"])
ax2.set_xlabel("Frequency (Hz)")
ax2.set_ylabel("Phase (degrees)")
ax2.grid(True, which='both', linestyle='--')

plt.tight_layout()
plt.show()
