a = b'hello'
print(a)
def ascii_to_hex(input_str):
    """
    將ASCII字符串轉換為16進制表示
    
    參數:
    - input_str (str): 輸入的ASCII字符串
    
    返回:
    - hex_str (str): 轉換後的16進制字符串
    """
    
    # 使用列表推導式將每個字符轉換為對應的16進制值
    hex_values = [hex(ord(char))[2:].zfill(2) for char in input_str]
    
    # 使用''.join()方法將列表中的16進制值組合成一個字符串
    hex_str = ''.join(hex_values)
    
    return hex_str

# 測試
if __name__ == '__main__':
    input_str = ":0103A6AC0001A9\r\n"
    hex_str = ascii_to_hex(input_str)
    print(f"ASCII input: {input_str}")
    print(f"Hex output: {hex_str}")