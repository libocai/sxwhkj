from gmssl import sm3, sm4
import json
import time
from urllib.parse import quote_plus

# 初始化加密密钥（保持与JS一致）
DECRYPTED_KEY = b"30062AFC48C0E7B5B0918851C0445A37"


def sm3_hash(message: str):
    """
    国密sm3加密
    :param message: 消息值，bytes类型
    :return: 哈希值
    """

    msg_list = [i for i in bytes(message.encode('UTF-8'))]
    hash_hex = sm3.sm3_hash(msg_list)
    return hash_hex

# SM3哈希函数
# def hash_data(data):
#     return sm3.sm3_hash(bytes(data, 'utf-8'))

# SM4加密函数
def encrypt_data(data):
    cipher = sm4.CryptSM4()
    cipher.set_key(DECRYPTED_KEY, sm4.SM4_ENCRYPT)
    encrypt_value = cipher.crypt_ecb(bytes(data, 'utf-8'))
    return encrypt_value.hex()

# SM4解密函数
def decrypt_data(encrypted_data):
    cipher = sm4.CryptSM4()
    cipher.set_key(DECRYPTED_KEY, sm4.SM4_DECRYPT)
    decrypt_value = cipher.crypt_ecb(bytes.fromhex(encrypted_data))
    return decrypt_value.decode('utf-8')

# 对象转查询字符串
def convert_object_to_query_string(json_str):
    data = json.loads(json_str)
    sorted_items = sorted(data.items(), key=lambda x: x[0])
    
    query_params = []
    for key, value in sorted_items:
        if value:
            encoded_key = quote_plus(key)
            if isinstance(value, dict):
                encoded_value = quote_plus(json.dumps(value, separators=(',', ':')))
            else:
                encoded_value = quote_plus(str(value))
            query_params.append(f"{encoded_key}={encoded_value}")
    
    return "&".join(query_params)

# 生成签名和时间戳
def generate_signature_and_timestamp(input_data=None):
    timestamp = int(time.time() * 1000)
    query_str = ""
    
    if input_data and 'parameter' in input_data:
        # 解密参数
        decrypted = decrypt_data(input_data['parameter'])
        params = json.loads(decrypted)
        params['timestamp'] = timestamp
        query_str = convert_object_to_query_string(json.dumps(params))
    else:
        params = input_data or {}
        params['timestamp'] = timestamp
        query_str = convert_object_to_query_string(json.dumps(params))
    
    # 添加固定key
    query_str += "&key=HD7232D2AAAKA@978D8723H211?IER&6"
    
    # 生成签名
    hashed = sm3_hash(query_str).upper()
    return {
        'sign': encrypt_data(hashed),
        'timestamp': encrypt_data(str(timestamp)),
        'source': "ZRCSL7V0JIRK1PHY"
    }

if __name__ == "__main__":
    # 测试请求
    payload = {
        "applyType": 1,
        "year": 2025,
        "pageNum": 10,
        "pageSize": 15
    }
    
    encrypted_data = {
        "parameter": encrypt_data(json.dumps(payload))
    }
    
    headers = generate_signature_and_timestamp(encrypted_data)
    print("生成的headers:", headers)
    
    import requests
    response = requests.post(
        "http://butiexitong.gagogroup.cn:8081/api/api/loginSidePageEDE/getPurchaseOfAgriculturalMachinery",
        headers={
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json;charset=UTF-8",
            **headers
        },
        json=encrypted_data
    )
    
    result = response.json()
    print("解密响应:", decrypt_data(result['data']))