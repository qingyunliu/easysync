def parse_os_info(os_info):
    """解析操作系统信息"""
    info = {}
    for line in os_info.split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            info[key.strip()] = value.strip().strip('"')
    return f"{info.get('PRETTY_NAME', 'Unknown')} ({info.get('VERSION_ID', 'Unknown')})"

def parse_cpu_info(cpu_info):
    """解析CPU信息"""
    info = {}
    for line in cpu_info.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()
    
    return [{
        'model': info.get('Model name', 'Unknown'),
        'cores': int(info.get('CPU(s)', 1)),
        'threads': int(info.get('Thread(s) per core', 1)),
        'frequency': info.get('CPU MHz', 'Unknown')
    }]

def parse_memory_info(memory_info):
    """解析内存信息"""
    lines = memory_info.split('\n')
    if len(lines) >= 2:
        headers = lines[0].split()
        values = lines[1].split()
        return {
            'total': int(values[1]),
            'used': int(values[2]),
            'free': int(values[3]),
            'shared': int(values[4]),
            'buffers': int(values[5]),
            'cached': int(values[6])
        }
    return {}

def parse_disk_info(disk_info):
    """解析磁盘信息"""
    disks = []
    lines = disk_info.split('\n')[1:]  # 跳过标题行
    for line in lines:
        if line.strip():
            parts = line.split()
            if len(parts) >= 6:
                disks.append({
                    'device': parts[0],
                    'mount': parts[5],
                    'total': int(parts[1]),
                    'used': int(parts[2]),
                    'free': int(parts[3]),
                    'usage': int(parts[4].rstrip('%'))
                })
    return disks

def parse_network_info(network_info):
    """解析网络信息"""
    interfaces = []
    current_interface = None
    
    for line in network_info.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # 检查是否是新的网络接口
        if ': ' in line and not line.startswith((' ', 'valid_lft')):
            if current_interface:
                interfaces.append(current_interface)
            
            # 解析接口名称和状态
            parts = line.split(': ')
            interface_name = parts[1].strip().split('@')[0]  # 处理可能的@符号
            
            current_interface = {
                'name': interface_name,
                'status': 'DOWN',  # 默认为DOWN，后面根据flags更新
                'ip': '',
                'mac': '',
                'mtu': '',
                'ipv6': []
            }
            
            # 解析状态和MTU
            if '<' in line and '>' in line:
                flags = line[line.find('<')+1:line.find('>')].split(',')
                current_interface['status'] = 'UP' if 'UP' in flags else 'DOWN'
                
            if 'mtu' in line.lower():
                mtu_match = line.lower().split('mtu')
                if len(mtu_match) > 1:
                    current_interface['mtu'] = mtu_match[1].split()[0]
        
        # 解析MAC地址
        elif 'link/ether' in line.lower() and current_interface:
            parts = line.split()
            if len(parts) >= 2:
                current_interface['mac'] = parts[1]
        
        # 解析IPv4地址
        elif 'inet ' in line and current_interface:
            parts = line.split()
            if len(parts) >= 2:
                current_interface['ip'] = parts[1].split('/')[0]
        
        # 解析IPv6地址
        elif 'inet6 ' in line and current_interface:
            parts = line.split()
            if len(parts) >= 2:
                ipv6 = parts[1].split('/')[0]
                if ipv6.startswith('fe80::'):
                    current_interface['ipv6'].append(ipv6)
    
    # 添加最后一个接口
    if current_interface:
        interfaces.append(current_interface)
    
    # 过滤掉没有IP地址和MAC地址的接口
    interfaces = [iface for iface in interfaces if iface['ip'] or iface['mac']]
    
    return interfaces

def parse_cpu_usage(cpu_info):
    """解析CPU使用率"""
    if cpu_info:
        parts = cpu_info.split()
        if len(parts) >= 8:
            return float(parts[1].strip('%'))
    return 0.0

def parse_memory_usage(memory_info):
    """解析内存使用率"""
    lines = memory_info.split('\n')
    if len(lines) >= 2:
        values = lines[1].split()
        if len(values) >= 3:
            total = int(values[1])
            used = int(values[2])
            return {
                'total': total,
                'used': used,
                'free': total - used,
                'usage_percent': (used / total) * 100
            }
    return {}

def parse_disk_usage(disk_info):
    """解析磁盘使用率"""
    usages = []
    lines = disk_info.split('\n')[1:]  # 跳过标题行
    for line in lines:
        if line.strip():
            parts = line.split()
            if len(parts) >= 5:
                usages.append({
                    'device': parts[0],
                    'mount_point': parts[5],
                    'total': parts[1],
                    'used': parts[2],
                    'free': parts[3],
                    'usage_percent': int(parts[4].rstrip('%'))
                })
    return usages

def parse_network_traffic(network_info):
    """解析网络流量"""
    traffic = {}
    lines = network_info.split('\n')[2:]  # 跳过标题行
    for line in lines:
        if ':' in line:
            interface, data = line.split(':', 1)
            interface = interface.strip()
            values = data.split()
            if len(values) >= 16:
                traffic[interface] = {
                    'rx_bytes': int(values[0]),
                    'tx_bytes': int(values[8]),
                    'rx_packets': int(values[1]),
                    'tx_packets': int(values[9])
                }
    return traffic

def parse_process_list(process_info):
    """解析进程列表"""
    processes = []
    lines = process_info.split('\n')
    headers = lines[0].split()
    for line in lines[1:]:
        if line.strip():
            parts = line.split()
            if len(parts) >= 11:
                processes.append({
                    'user': parts[0],
                    'pid': int(parts[1]),
                    'cpu_percent': float(parts[2]),
                    'memory_percent': float(parts[3]),
                    'vsz': parts[4],
                    'rss': parts[5],
                    'tty': parts[6],
                    'stat': parts[7],
                    'start': parts[8],
                    'time': parts[9],
                    'command': ' '.join(parts[10:])
                })
    return processes