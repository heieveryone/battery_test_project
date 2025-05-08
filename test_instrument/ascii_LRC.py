def calc_lrc(hex_str: str) -> str:
    """
    计算 Modbus ASCII 帧的 LRC 校验码。

    参数:
        hex_str: 不含起始':'和结束CRLF的十六进制字符串,
                 例如 "01050805FF00"

    返回:
        两位十六进制字符串形式的 LRC 校验码, 例如 "EE"
    """
    data = bytes.fromhex(hex_str)
    total = sum(data)
    # LRC = (−总和) mod 256
    lrc = ((-total) & 0xFF)
    return f"{lrc:02X}"

def build_modbus_ascii_frame(hex_str: str) -> str:
    """
    构建完整的 Modbus ASCII 帧，附加 ':' 前缀和 LRC + CRLF 结束符。

    参数:
        hex_str: 关键数据部分, 例如 "01050805FF00"
    返回:
        完整 ASCII 帧, 例如 ":01050805FF00EE\r\n"
    """
    lrc = calc_lrc(hex_str)
    return f":{hex_str}{lrc}\r\n"

# 示例
if __name__ == "__main__":
    payload = "01050808FF00"
    print("Payload:", payload)
    print("LRC:", calc_lrc(payload))
    print("Full frame:", build_modbus_ascii_frame(payload))
