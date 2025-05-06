import subprocess
import socket
import ipaddress

class NetPulse:
    def format_output(self, data: dict) -> str:
        if not isinstance(data, dict):
            return str(data)
        lines = []
        for k, v in data.items():
            lines.append(f"{k.replace('_', ' ').capitalize()}: {v}")
        return "\n".join(lines)

    def ping(self, host, count=4, continuous=False):
        try:
            args = ["ping", host]
            if continuous:
                args += ["-t"]
            else:
                args += ["-n", str(count)]
            result = subprocess.run(args, capture_output=True, text=True)
            return {
                "host": host,
                "success": "TTL=" in result.stdout,
                "output": result.stdout.strip()
            }
        except Exception as e:
            return {"host": host, "success": False, "error": str(e)}

    def traceroute(self, host):
        try:
            result = subprocess.run(["tracert", host], capture_output=True, text=True)
            return {"host": host, "output": result.stdout.strip()}
        except Exception as e:
            return {"host": host, "error": str(e)}

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
            return {"domain": domain, "error": str(e)}

    def calc_subnet_info(self, ip_str, mask_str):
        ip = ipaddress.IPv4Address(ip_str)
        net = ipaddress.IPv4Network(f"{ip_str}/{mask_str}", strict=False)
        wildcard = ipaddress.IPv4Address(int(net.hostmask))
        return {
            "ip address": str(ip),
            "subnet mask": str(net.netmask),
            "wildcard mask": str(wildcard),
            "cidr notation": str(net),
            "network address": str(net.network_address),
            "broadcast address": str(net.broadcast_address),
            "first usable": str(list(net.hosts())[0]) if net.num_addresses > 2 else "N/A",
            "last usable": str(list(net.hosts())[-1]) if net.num_addresses > 2 else "N/A",
            "usable host count": len(list(net.hosts())),
            "ip class": self.get_ip_class(ip),
            "is private": ip.is_private
        }

    def get_ip_class(self, ip):
        first_octet = int(str(ip).split('.')[0])
        if 1 <= first_octet <= 126:
            return 'A'
        elif 128 <= first_octet <= 191:
            return 'B'
        elif 192 <= first_octet <= 223:
            return 'C'
        elif 224 <= first_octet <= 239:
            return 'D (Multicast)'
        elif 240 <= first_octet <= 255:
            return 'E (Experimental)'
        return 'Unknown'

    def scan_network(self, network_cidr):
        net = ipaddress.IPv4Network(network_cidr, strict=False)
        return [str(ip) for ip in net.hosts()]