import paramiko
import io
from typing import Optional, Tuple, Union
from backend.app.models import Client, Node

class SSHClient:
    def __init__(self, client: Optional[Client] = None, node: Optional[Node] = None):
        if client:
            self.client = client
            self.port = client.port
            self.username = client.username
            self.hostname = client.hostname
            self.password = client.password
            self.ssh_key = client.ssh_key
            self.ip_address = client.ip_address
            self.auth_type = client.auth_type

        elif node:
            self.node = node
            self.port = node.port
            self.username = node.username
            self.hostname = node.name
            self.password = node.password
            self.ssh_key = node.auth_key
            self.ip_address = node.ipaddress
            self.auth_type = node.auth_type

        self._ssh = None
        self._sftp = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """建立SSH连接"""
        if self._ssh is not None:
            return

        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if self.auth_type == 'password':
                self._ssh.connect(
                    hostname=self.ip_address,
                    port=self.port,
                    username=self.username,
                    password=self.password
                )
            else:
                pkey = paramiko.RSAKey.from_private_key(
                    io.StringIO(self.ssh_key)
                )
                self._ssh.connect(
                    hostname=self.ip_address,
                    port=self.port,
                    username=self.username,
                    pkey=pkey
                )
        except Exception as e:
            self.close()
            raise ConnectionError(f"SSH连接失败: {str(e)}")

    def get_sftp(self):
        """获取SFTP客户端"""
        if self._sftp is None:
            if self._ssh is None:
                self.connect()
            self._sftp = self._ssh.open_sftp()
        return self._sftp

    def execute_command(self, command: str) -> Tuple[str, str, int]:
        """
        执行SSH命令
        返回: (stdout, stderr, exit_code)
        """
        if self._ssh is None:
            self.connect()

        stdin, stdout, stderr = self._ssh.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        return stdout.read().decode(), stderr.read().decode(), exit_code

    def upload_file(self, local_path: str, remote_path: str):
        """上传文件到远程服务器"""
        sftp = self.get_sftp()
        sftp.put(local_path, remote_path)

    def download_file(self, remote_path: str, local_path: str):
        """从远程服务器下载文件"""
        sftp = self.get_sftp()
        sftp.get(remote_path, local_path)

    def create_directory(self, path: str):
        """在远程服务器创建目录（支持多层目录）"""
        sftp = self.get_sftp()
        try:
            # 分割路径
            path_parts = path.strip('/').split('/')
            current_path = ''
            
            # 逐层创建目录
            for part in path_parts:
                if current_path:
                    current_path += '/' + part
                else:
                    current_path = '/' + part
                
                try:
                    sftp.stat(current_path)  # 检查目录是否存在
                except IOError:
                    # 目录不存在，创建它
                    try:
                        sftp.mkdir(current_path)
                        print(f"Created directory: {current_path}")
                    except IOError as e:
                        print(f"Failed to create directory {current_path}: {e}")
                        raise
        except Exception as e:
            print(f"Error creating directory {path}: {e}")
            raise

    def write_file(self, remote_path: str, content: str):
        """写入文件内容到远程服务器"""
        sftp = self.get_sftp()
        with sftp.file(remote_path, 'w') as f:
            f.write(content)

    def read_file(self, remote_path: str) -> str:
        """读取远程服务器上的文件内容"""
        sftp = self.get_sftp()
        with sftp.file(remote_path, 'r') as f:
            return f.read().decode()

    def close(self):
        """关闭SSH连接"""
        if self._sftp:
            self._sftp.close()
            self._sftp = None
        if self._ssh:
            self._ssh.close()
            self._ssh = None 