import requests
import dns.resolver
import os
import time
import sys
import socket

ACMEDNS_URL = os.environ.get("ACMEDNS_URL", "http://localhost:80")
DNS_SERVER = os.environ.get("DNS_SERVER", "localhost")
DNS_PORT = int(os.environ.get("DNS_PORT", 53))

def wait_for_server():
    print(f"Waiting for acme-dns at {ACMEDNS_URL}...")
    for i in range(30):
        try:
            resp = requests.get(f"{ACMEDNS_URL}/health")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "healthy":
                    print("Server is up and healthy!")
                    return True
        except:
            pass
        time.sleep(1)
    return False

def test_metrics():
    print("Testing metrics...")
    resp = requests.get(f"{ACMEDNS_URL}/metrics")
    if resp.status_code != 200:
        print(f"Failed to get metrics: {resp.status_code}")
        return False
    
    metrics = resp.text
    if "acmedns_challenge_success_total" not in metrics:
        print("Metric acmedns_challenge_success_total missing")
        return False
    if "acmedns_challenge_failure_total" not in metrics:
        print("Metric acmedns_challenge_failure_total missing")
        return False
    print("Metrics are present")
    return True

def get_success_count():
    resp = requests.get(f"{ACMEDNS_URL}/metrics")
    for line in resp.text.splitlines():
        if line.startswith("acmedns_challenge_success_total"):
            return float(line.split()[1])
    return 0.0

def test_flow():
    # 0. Initial metrics check
    if not test_metrics():
        return False
    
    initial_success = get_success_count()

    # 1. Register account
    print("Registering account...")
    resp = requests.post(f"{ACMEDNS_URL}/register")
    if resp.status_code != 201:
        print(f"Failed to register: {resp.status_code} {resp.text}")
        return False
    
    account = resp.json()
    username = account['username']
    api_key = account['password']
    subdomain = account['subdomain']
    fulldomain = account['fulldomain']
    print(f"Registered subdomain: {subdomain}")

    # 2. Update TXT records
    headers = {
        "X-Api-User": username,
        "X-Api-Key": api_key
    }

    txt_values = ["secret_token_1", "secret_token_2"]
    
    for val in txt_values:
        print(f"Updating TXT record with value: {val}")
        # Let's Encrypt uses 43 char tokens usually, but our validation is flexible now (or we use a dummy one)
        # Actually our current validation in pkg/api/util.go still expects 43 chars if I recall correctly
        # Let's use 43 chars just in case
        dummy_val = val.ljust(43, '_')[:43]
        payload = {
            "subdomain": subdomain,
            "txt": dummy_val
        }
        resp = requests.post(f"{ACMEDNS_URL}/update", headers=headers, json=payload)
        if resp.status_code != 200:
            print(f"Failed to update: {resp.status_code} {resp.text}")
            return False
        
    print("Updates successful. Waiting for DNS propagation (local cache)...")
    time.sleep(2)

    # 3. Verify DNS resolution
    print(f"Resolving TXT records for {fulldomain}...")
    
    # Resolve hostname to IP if needed
    try:
        dns_server_ip = socket.gethostbyname(DNS_SERVER)
    except:
        dns_server_ip = DNS_SERVER

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server_ip]
    resolver.port = DNS_PORT

    try:
        answers = resolver.resolve(fulldomain, "TXT")
        resolved_values = [str(rdata).strip('"') for rdata in answers]
        print(f"Resolved values: {resolved_values}")
        
        # Check if both are present
        for val in txt_values:
            dummy_val = val.ljust(43, '_')[:43]
            if dummy_val not in resolved_values:
                print(f"Expected value {dummy_val} not found in resolved values")
                return False
    except Exception as e:
        print(f"DNS resolution failed: {e}")
        return False

    # 4. Verify metric increase
    print("Verifying success count increase...")
    final_success = get_success_count()
    if final_success <= initial_success:
        print(f"Expected success count to increase (initial: {initial_success}, final: {final_success})")
        return False
    print(f"Success count increased from {initial_success} to {final_success}")

    print("E2E Test Passed Successfully!")
    return True

if __name__ == "__main__":
    if not wait_for_server():
        print("Server timed out.")
        sys.exit(1)
    
    if not test_flow():
        sys.exit(1)
    
    sys.exit(0)
