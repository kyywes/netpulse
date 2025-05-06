import subprocess
import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed

class NetPulse:
    def __init__(self, max_threads=100, ping_timeout=1000):
        self.max_threads = max_threads
        self.ping_timeout = ping_timeout  # ms

    def ping(self, host, count=4):
        try:
            result = subprocess.run(
                ["ping", "-n", str(count), "-w", str(self.ping_timeout), host],
                capture_output=True, text=True, check=False
            )
            return {
                "host": host,
                "success": "TTL=" in result.stdout,
                "output": result.stdout.strip()
            }
        except Exception as e:
            return {
                "host": host,
                "success": False,
                "error": str(e)
            }

    def traceroute(self, host):
        try:
            result = subprocess.run(
                ["tracert", host],
                capture_output=True, text=True, check=False
            )
            return {
                "host": host,
                "output": result.stdout.strip()
            }
        except Exception as e:
            return {
                "host": host,
                "error": str(e)
            }

    def nslookup(self, domain):
        try:
            result = socket.gethostbyname_ex(domain)
            return {
                "domain": domain,
                "hostname": result[0],
                "aliases": result[1],
                "addresses": result[2]
            }
        except Exception as e:
            return {
                "domain": domain,
                "error": str(e)
            }

    def calc_subnet_info(self, ip_mask: str):
        try:
            ip_str, mask_str = ip_mask.strip().split()
            ip = ipaddress.IPv4Address(ip_str)
            net = ipaddress.IPv4Network(f"{ip_str}/{mask_str}", strict=False)

            wildcard = str(ipaddress.IPv4Address(int(net.hostmask)))
            return {
                "ip_address": str(ip),
                "subnet_mask": mask_str,
                "wildcard_mask": wildcard,
                "cidr_notation": str(net.with_prefixlen),
                "network_address": str(net.network_address),
                "broadcast_address": str(net.broadcast_address),
                "first_usable": str(list(net.hosts())[0]) if net.num_addresses > 2 else str(net.network_address),
                "last_usable": str(list(net.hosts())[-1]) if net.num_addresses > 2 else str(net.broadcast_address),
                "usable_host_count": len(list(net.hosts())),
                "ip_class": self._get_ip_class(ip),
                "is_private": net.is_private
            }
        except Exception as e:
            return {"error": str(e)}

    def scan_network(self, network_cidr: str):
        try:
            net = ipaddress.IPv4Network(network_cidr, strict=False)
            results = []

            def check_host(ip):
                result = subprocess.run(
                    ["ping", "-n", "1", "-w", str(self.ping_timeout), str(ip)],
                    capture_output=True, text=True
                )
                if "TTL=" in result.stdout:
                    return str(ip)
                return None

            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                futures = {executor.submit(check_host, ip): ip for ip in net.hosts()}
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        results.append(res)

            return {
                "network": network_cidr,
                "alive_hosts": results,
                "count": len(results)
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_ip_class(self, ip):
        first_octet = int(str(ip).split('.')[0])
        if 1 <= first_octet <= 126:
            return "A"
        elif 128 <= first_octet <= 191:
            return "B"
        elif 192 <= first_octet <= 223:
            return "C"
        elif 224 <= first_octet <= 239:
            return "D (Multicast)"
        elif 240 <= first_octet <= 254:
            return "E (Experimental)"
        return "Unknown"