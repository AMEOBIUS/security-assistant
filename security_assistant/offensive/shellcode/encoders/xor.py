"""
XOR Encoder
Simple XOR encoder for shellcode obfuscation
"""

from typing import Union


class XOREncoder:
    """
    XOR encoder for shellcode obfuscation.
    
    Args:
        key: XOR key (single byte or multi-byte)
    """
    
    def __init__(self, key: Union[int, bytes] = 0xAA):
        if isinstance(key, int):
            self.key = bytes([key])
        else:
            self.key = key
    
    def encode(self, data: bytes) -> bytes:
        """
        XOR encode data.
        
        Args:
            data: Data to encode
            
        Returns:
            Encoded data
        """
        encoded = bytearray()
        key_len = len(self.key)
        
        for i, byte in enumerate(data):
            key_byte = self.key[i % key_len]
            encoded.append(byte ^ key_byte)
        
        return bytes(encoded)
    
    def decode(self, data: bytes) -> bytes:
        """
        XOR decode data (same as encode for XOR).
        
        Args:
            data: Data to decode
            
        Returns:
            Decoded data
        """
        return self.encode(data)  # XOR is symmetric


def xor_encode(data: bytes, key: Union[int, bytes] = 0xAA) -> bytes:
    """
    Convenience function for XOR encoding.
    
    Args:
        data: Data to encode
        key: XOR key
        
    Returns:
        Encoded data
    """
    encoder = XOREncoder(key)
    return encoder.encode(data)


def xor_decode(data: bytes, key: Union[int, bytes] = 0xAA) -> bytes:
    """
    Convenience function for XOR decoding.
    
    Args:
        data: Data to decode
        key: XOR key
        
    Returns:
        Decoded data
    """
    encoder = XOREncoder(key)
    return encoder.decode(data)
