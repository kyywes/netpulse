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