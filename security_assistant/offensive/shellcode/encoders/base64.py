"""
Base64 Encoder
Base64 encoder for shellcode obfuscation
"""

import base64


class Base64Encoder:
    """
    Base64 encoder for shellcode obfuscation.
    """
    
    def encode(self, data: bytes) -> bytes:
        """
        Base64 encode data.
        
        Args:
            data: Data to encode
            
        Returns:
            Encoded data as bytes
        """
        encoded = base64.b64encode(data)
        return encoded
    
    def decode(self, data: bytes) -> bytes:
        """
        Base64 decode data.
        
        Args:
            data: Data to decode
            
        Returns:
            Decoded data
        """
        return base64.b64decode(data)


def base64_encode(data: bytes) -> bytes:
    """
    Convenience function for Base64 encoding.
    
    Args:
        data: Data to encode
        
    Returns:
        Encoded data
    """
    encoder = Base64Encoder()
    return encoder.encode(data)


def base64_decode(data: bytes) -> bytes:
    """
    Convenience function for Base64 decoding.
    
    Args:
        data: Data to decode
        
    Returns:
        Decoded data
    """
    encoder = Base64Encoder()
    return encoder.decode(data)
