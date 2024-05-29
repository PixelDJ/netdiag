import subprocess
import json
import platform
import time
from datetime import datetime

# Color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_result(message, result_type):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if result_type == "warning":
        color_code = YELLOW
        label = "[WARN]"
    elif result_type == "info":
        color_code = ""
        label = "[INFO]"
    elif result_type == "success":
        color_code = GREEN
        label = "[INFO]"
    elif result_type == "failure":
        color_code = RED
        label = "[FAIL]"
    else:
        color_code = ""
        label = "[INFO]"
    
    print(f"{timestamp} {color_code}{label} {message}{RESET}")

def ping(ip):
    system = platform.system()
    if system == "Windows":
        command = ["ping", "-n", "1", ip]
    else:  # Assuming Unix-based system
        command = ["ping", "-c", "1", ip]
    
    try:
        output = subprocess.check_output(command, universal_newlines=True)
        if "unreachable" in output.lower():
            return False
        if system == "Windows":
            if "TTL=" in output:
                return True
        else:
            if "1 received" in output:
                return True
        return False
    except subprocess.CalledProcessError:
        return False

def check_connectivity(config):
    statuses = {}
    warnings = []

    external_test_ip = config["external_test_ip"]
    external_test_ip2 = config["external_test_ip2"]
    internal_dc1 = config["internal_dc1"]
    internal_dc2 = config["internal_dc2"]
    dns_forwarder = config["dns_forwarder"]
    firewall_ip = config["firewall_ip"]
    wap = config["wap"]
    wifi_controller = config["wifi_controller"]
    core_switch = config["core_switch"]

    if not ping(firewall_ip):
        statuses["firewall"] = "down"
        return statuses

    if not ping(firewall_ip):
        statuses["firewall"] = "down"
        return statuses

    if not ping(core_switch):
        statuses["core_switch"] = "down"
        return statuses
    else:
        statuses["core_switch"] = "reachable"

    if not ping(internal_dc1):
        if not ping(internal_dc2):
            statuses["dc"] = "both down"
            return statuses
        else:
            warnings.append("Primary DC down")
            statuses["internal_dc1"] = "down"
    else:
        statuses["internal_dc1"] = "reachable"

    if not ping(internal_dc2):
        warnings.append("Second DC down")
        statuses["internal_dc2"] = "down"
    else:
        statuses["internal_dc2"] = "reachable"

    if not ping(dns_forwarder):
        statuses["dns_forwarder"] = "down"
        return statuses
    else:
        statuses["dns_forwarder"] = "reachable"

    if not ping(wap):
        warnings.append("WAP down")
        statuses["wap"] = "down"
    else:
        statuses["wap"] = "reachable"

    if not ping(wifi_controller):
        warnings.append("WiFi Controller down")
        statuses["wifi_controller"] = "down"
    else:
        statuses["wifi_controller"] = "reachable"

    if not ping(external_test_ip):
        statuses["external_test_ip"] = "not reachable"
        if not ping(external_test_ip2):
            statuses["external_test_ip2"] = "not reachable"
        else:
            statuses["external_test_ip2"] = "reachable"
    else:
        statuses["external_test_ip"] = "reachable"

    if warnings:
        statuses["warnings"] = warnings
    else:
        statuses["warnings"] = "none"

    statuses["status"] = "everything ok"
    return statuses

def main():
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    
    last_statuses = {}

    while True:
        current_statuses = check_connectivity(config)
        # print(current_statuses)  # Debugging
        if current_statuses != last_statuses:
            if "core_switch" in current_statuses and current_statuses["core_switch"] == "down":
                print_result("Core switch down", "failure")
            elif "firewall" in current_statuses and current_statuses["firewall"] == "down":
                print_result("Firewall down", "failure")
            elif "dc" in current_statuses and current_statuses["dc"] == "both down":
                print_result("No DC available", "failure")
            elif "dns_forwarder" in current_statuses and current_statuses["dns_forwarder"] == "down":
                print_result("DNS server down", "failure")
            elif "external_test_ip" in current_statuses and current_statuses["external_test_ip"] == "not reachable":
                if "external_test_ip2" in current_statuses and current_statuses["external_test_ip2"] == "not reachable":
                    print_result("External test IPs not reachable", "failure")
                else:
                    print_result("The first external test IP is not reachable", "warning")
            else:
                warnings = current_statuses.get("warnings", [])
                if warnings != "none":
                    for warning in warnings:
                        print_result(warning, "warning")
                else:
                    print_result("Everything is OK", "success")
            last_statuses = current_statuses
        time.sleep(5)

if __name__ == "__main__":
    main()