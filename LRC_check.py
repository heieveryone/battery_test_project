def calculate_lrc(data):
    """計算ASCII LRC（Longitudinal Redundancy Check）"""
    lrc = 0
    for byte in data:
        lrc = (lrc - byte) & 0xFF
    return lrc

if __name__ == "__main__":
    # 測試數據，例如 [0x01, 0x03, 0x00, 0x01]
    data = [0x01, 0x05, 0x05, 0x00, 0x00, 0x00]
    
    lrc_value = calculate_lrc(data)
    print(f"ASCII LRC: {lrc_value:02X}")