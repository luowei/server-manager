import socket
import struct
import re
from typing import Optional
import logging
from wakeonlan import send_magic_packet

logger = logging.getLogger(__name__)


class WOLManager:
    """Wake-on-LAN管理器"""
    
    @staticmethod
    def validate_mac_address(mac: str) -> str:
        """
        验证并标准化MAC地址格式
        
        Args:
            mac: MAC地址字符串
            
        Returns:
            标准化的MAC地址 (XX:XX:XX:XX:XX:XX格式)
            
        Raises:
            ValueError: MAC地址格式错误
        """
        # 移除所有分隔符并转换为大写
        clean_mac = re.sub(r'[:\-\.]', '', mac.upper())
        
        # 验证长度和字符
        if len(clean_mac) != 12:
            raise ValueError(f"MAC地址长度错误: {mac}")
        
        if not re.match(r'^[0-9A-F]{12}$', clean_mac):
            raise ValueError(f"MAC地址包含无效字符: {mac}")
        
        # 格式化为标准格式
        return ':'.join([clean_mac[i:i+2] for i in range(0, 12, 2)])
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """
        验证IP地址格式
        
        Args:
            ip: IP地址字符串
            
        Returns:
            是否为有效的IP地址
        """
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False
    
    @staticmethod
    def send_wol_packet(mac_address: str, ip_address: Optional[str] = None, port: int = 9) -> bool:
        """
        发送WOL魔术包
        
        Args:
            mac_address: 目标设备的MAC地址
            ip_address: 广播IP地址、IP地址或CIDR，默认为255.255.255.255
            port: WOL端口，默认为9
            
        Returns:
            是否成功发送
        """
        try:
            # 验证MAC地址
            mac = WOLManager.validate_mac_address(mac_address)
            
            # 计算广播地址
            broadcast_address = WOLManager.get_broadcast_address_smart(ip_address)
            
            # 使用wakeonlan库发送魔术包
            send_magic_packet(mac, ip_address=broadcast_address, port=port)
            
            logger.info(f"WOL包已发送到 {mac} (广播地址: {broadcast_address}, Port: {port})")
            return True
            
        except Exception as e:
            logger.error(f"发送WOL包失败: {e}")
            return False
    
    @staticmethod
    def create_magic_packet(mac_address: str) -> bytes:
        """
        创建WOL魔术包
        
        Args:
            mac_address: MAC地址
            
        Returns:
            魔术包字节数据
        """
        # 验证并格式化MAC地址
        mac = WOLManager.validate_mac_address(mac_address)
        
        # 将MAC地址转换为字节
        mac_bytes = bytes.fromhex(mac.replace(':', ''))
        
        # 创建魔术包: 6个0xFF + 16次重复的MAC地址
        magic_packet = b'\xFF' * 6 + mac_bytes * 16
        
        return magic_packet
    
    @staticmethod
    def send_raw_wol_packet(mac_address: str, ip_address: Optional[str] = None, port: int = 9) -> bool:
        """
        使用原始socket发送WOL包
        
        Args:
            mac_address: 目标设备的MAC地址
            ip_address: 广播IP地址
            port: WOL端口
            
        Returns:
            是否成功发送
        """
        try:
            # 创建魔术包
            magic_packet = WOLManager.create_magic_packet(mac_address)
            
            # 创建UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # 确定目标地址
            target_ip = ip_address if ip_address else '255.255.255.255'
            
            # 发送魔术包
            sock.sendto(magic_packet, (target_ip, port))
            sock.close()
            
            logger.info(f"原始WOL包已发送到 {mac_address} (IP: {target_ip}, Port: {port})")
            return True
            
        except Exception as e:
            logger.error(f"发送原始WOL包失败: {e}")
            return False
    
    @staticmethod
    def ping_host(hostname_or_ip: str, timeout: int = 3) -> bool:
        """
        Ping主机检查是否在线（兼容Docker容器环境）
        
        Args:
            hostname_or_ip: 主机名或IP地址
            timeout: 超时时间（秒）
            
        Returns:
            主机是否在线
        """
        # 首先尝试TCP连接检查（适用于Docker环境）
        if WOLManager.tcp_ping(hostname_or_ip, timeout):
            return True
        
        # 然后尝试传统ICMP ping
        return WOLManager.icmp_ping(hostname_or_ip, timeout)
    
    @staticmethod
    def tcp_ping(hostname_or_ip: str, timeout: int = 3) -> bool:
        """
        使用TCP连接检查主机是否在线（Docker友好）
        
        Args:
            hostname_or_ip: 主机名或IP地址
            timeout: 超时时间（秒）
            
        Returns:
            主机是否在线
        """
        import socket
        
        # 常见端口列表，用于检测主机是否在线
        common_ports = [22, 23, 53, 80, 135, 139, 443, 445, 993, 995, 3389, 5900]
        
        try:
            # 先解析主机名到IP地址
            try:
                target_ip = socket.gethostbyname(hostname_or_ip)
                logger.debug(f"解析 {hostname_or_ip} -> {target_ip}")
            except socket.gaierror:
                logger.debug(f"无法解析主机名: {hostname_or_ip}")
                return False
            
            # 尝试连接常见端口
            for port in common_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout / len(common_ports))  # 分配超时时间
                    result = sock.connect_ex((target_ip, port))
                    sock.close()
                    
                    if result == 0:
                        logger.debug(f"TCP连接成功: {hostname_or_ip}:{port}")
                        return True
                        
                except Exception as e:
                    logger.debug(f"TCP连接失败 {hostname_or_ip}:{port} - {e}")
                    continue
            
            logger.debug(f"所有TCP端口连接失败: {hostname_or_ip}")
            return False
            
        except Exception as e:
            logger.error(f"TCP ping失败: {e}")
            return False
    
    @staticmethod
    def icmp_ping(hostname_or_ip: str, timeout: int = 3) -> bool:
        """
        传统ICMP ping检查
        
        Args:
            hostname_or_ip: 主机名或IP地址
            timeout: 超时时间（秒）
            
        Returns:
            主机是否在线
        """
        import subprocess
        import platform
        
        try:
            # 根据操作系统选择ping命令参数
            system = platform.system().lower()
            if system == "windows":
                cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), hostname_or_ip]
            else:
                cmd = ["ping", "-c", "1", "-W", str(timeout), hostname_or_ip]
            
            # 执行ping命令
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 1)
            success = result.returncode == 0
            
            if success:
                logger.debug(f"ICMP ping成功: {hostname_or_ip}")
            else:
                logger.debug(f"ICMP ping失败: {hostname_or_ip}")
                
            return success
            
        except Exception as e:
            logger.error(f"ICMP ping失败: {e}")
            return False
    
    @staticmethod
    def resolve_hostname_to_ip(hostname: str) -> Optional[str]:
        """
        解析主机名到IP地址
        
        Args:
            hostname: 主机名
            
        Returns:
            IP地址或None
        """
        try:
            ip = socket.gethostbyname(hostname)
            return ip
        except socket.gaierror as e:
            logger.error(f"解析主机名失败: {hostname} -> {e}")
            return None
    
    @staticmethod
    def get_broadcast_address(ip: str, netmask: str = "255.255.255.0") -> str:
        """
        计算广播地址
        
        Args:
            ip: IP地址
            netmask: 子网掩码
            
        Returns:
            广播地址
        """
        try:
            # 将IP和子网掩码转换为整数
            ip_int = struct.unpack("!I", socket.inet_aton(ip))[0]
            mask_int = struct.unpack("!I", socket.inet_aton(netmask))[0]
            
            # 计算广播地址
            broadcast_int = ip_int | (~mask_int & 0xFFFFFFFF)
            
            # 转换回字符串
            broadcast = socket.inet_ntoa(struct.pack("!I", broadcast_int))
            return broadcast
            
        except Exception as e:
            logger.error(f"计算广播地址失败: {e}")
            return "255.255.255.255"
    
    @staticmethod
    def get_broadcast_address_smart(ip_address: Optional[str] = None) -> str:
        """
        智能计算广播地址
        
        Args:
            ip_address: IP地址、CIDR或None（自动检测本机网络）
            
        Returns:
            广播地址
        """
        import ipaddress
        
        try:
            if not ip_address:
                # 未指定IP地址，使用本机网络接口
                return WOLManager.get_local_broadcast_address()
            
            if '/' in ip_address:
                # CIDR格式
                network = ipaddress.ip_network(ip_address, strict=False)
                return str(network.broadcast_address)
            else:
                # 纯IP地址，默认/24子网掩码
                network = ipaddress.ip_network(f"{ip_address}/24", strict=False)
                return str(network.broadcast_address)
                
        except Exception as e:
            logger.error(f"智能计算广播地址失败: {e}")
            return "255.255.255.255"
    
    @staticmethod
    def get_local_broadcast_address() -> str:
        """
        获取本机网络的广播地址
        
        Returns:
            本机网络的广播地址
        """
        import psutil
        import ipaddress
        
        try:
            # 获取网络接口信息
            interfaces = psutil.net_if_addrs()
            
            for interface, addrs in interfaces.items():
                # 跳过回环接口
                if interface.startswith('lo'):
                    continue
                    
                ipv4_addr = None
                netmask = None
                
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        ipv4_addr = addr.address
                        netmask = addr.netmask
                        break
                
                if ipv4_addr and netmask and not ipv4_addr.startswith('169.254'):
                    # 计算网络地址和广播地址
                    network = ipaddress.ip_network(f"{ipv4_addr}/{netmask}", strict=False)
                    return str(network.broadcast_address)
            
            # 如果没有找到合适的接口，返回默认广播地址
            return "255.255.255.255"
            
        except Exception as e:
            logger.error(f"获取本机网络广播地址失败: {e}")
            return "255.255.255.255"