
def parse_modbus_ascii_response(response):
    """
    解析Modbus從站回傳的ASCII碼
    
    參數:
    - response (str): 從站回傳的ASCII碼字符串
    
    返回:
    - parsed_data (dict): 解析後的數據字典
    """
    
    # 移除起始字符 ':' 和結束字符 '\r\n'
    response = response.strip(':').strip('\r\n')
    
    # 解析地址
    address = int(response[0:2], 16) if response[0:2] else None
    
    # 解析功能碼
    function_code = int(response[2:4], 16) if response[2:4] else None
    
    # 解析資料長度（字節數）
    data_length = int(response[4:6], 16) if response[4:6] else None
    
    # 解析資料
    data = []
    if response[6:]:
        for i in range(6, 6 + data_length*2, 2):
            if response[i:i+2]:
                data.append(int(response[i:i+2], 16))
    
    # 解析LRC校驗值
    lrc = response[-2:] if response[-2:] else None
    
    # 組合解析後的數據字典
    parsed_data = {
        'Address': address,
        'Function Code': function_code,
        'Data Length': data_length,
        'Data': data,
        'LRC': lrc
    }
    
    return parsed_data

# 測試
if __name__ == '__main__':
    response = ":0103020136C3\r\n"  # 示例的Modbus ASCII回傳碼
    parsed_data = parse_modbus_ascii_response(response)
    print(parsed_data)