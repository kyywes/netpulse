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
        
import subprocess
import ipaddress
import socket
import json
from concurrent.futures import ThreadPoolExecutor

def mask_to_cidr(mask_str):
    return sum([bin(int(x)).count('1') for x in mask_str.split('.')])

def wildcard_mask(mask_str):
    return ".".join(str(255 - int(octet)) for octet in mask_str.split('.'))

def ip_class(ip):
    first = int(ip.split('.')[0])
    if first <= 127: return "A"
    elif first <= 191: return "B"
    elif first <= 223: return "C"
    elif first <= 239: return "D (Multicast)"
    else: return "E (Experimental)"

class NetPulse:
    def ping(self, host, continuous=False):
        cmd = ['ping', host]
        if continuous: cmd.insert(1, '-t')
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def traceroute(self, host):
        result = subprocess.run(['tracert', host], capture_output=True, text=True)
        return result.stdout

    def nslookup(self, domain):
        ip = socket.gethostbyname(domain)
        return json.dumps({"domain": domain, "ip": ip}, indent=2)

    def subnet_info(self, input_str):
        ip_str, mask_str = input_str.strip().split()
        cidr = mask_to_cidr(mask_str)
        net = ipaddress.IPv4Network(f"{ip_str}/{cidr}", strict=False)
        hosts = list(net.hosts())
        return json.dumps({
            "ip_address": ip_str,
            "subnet_mask": mask_str,
            "wildcard_mask": wildcard_mask(mask_str),
            "cidr_notation": f"{net.network_address}/{cidr}",
            "network_address": str(net.network_address),
            "broadcast_address": str(net.broadcast_address),
            "first_usable": str(hosts[0]) if hosts else "N/A",
            "last_usable": str(hosts[-1]) if hosts else "N/A",
            "usable_host_count": len(hosts),
            "ip_class": ip_class(ip_str),
            "is_private": net.is_private,
        }, indent=2)

    def scan(self, cidr):
        net = ipaddress.ip_network(cidr, strict=False)
        hosts = list(net.hosts())
        found = []

        def ping_ip(ip):
            try:
                result = subprocess.run(['ping', '-n', '1', '-w', '800', str(ip)],
                                        capture_output=True, text=True)
                if "TTL=" in result.stdout:
                    found.append(str(ip))
            except:
                pass

        with ThreadPoolExecutor(max_workers=100) as executor:
            executor.map(ping_ip, hosts)

        return json.dumps({"active_hosts": found}, indent=2) if found else "Nessun host attivo rilevato."