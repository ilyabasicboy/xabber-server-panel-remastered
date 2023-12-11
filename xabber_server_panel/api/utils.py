def token_to_int(token: str) -> int:
    return int(''.join([str(ord(char)).rjust(3, '0') for char in token]))


def int_to_token(number: int) -> str:
    hash_token = str(number).rjust((len(str(number)) + 2) // 3 * 3, '0')
    return ''.join([chr(int(hash_token[i:i+3])) for i in range(0, len(hash_token), 3)])
