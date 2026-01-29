import os, requests

CF_TOKENS = [t.strip() for t in os.getenv("CF_TOKENS", "").split(",") if t.strip()]
# yx 读远程，py 读刚才生成的本地文件
CONFIGS = {
    "yx": "https://github.com/anlish01/cfipcaiji/raw/refs/heads/main/ip.txt",
    "py": "filtered_ips.txt" 
}

def cf_api(endpoint, token, method="GET", data=None):
    url = f"https://api.cloudflare.com/client/v4/{endpoint}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.request(method, url, headers=headers, json=data)
    return res.json()

def main():
    for token in CF_TOKENS:
        try:
            zone = cf_api("zones", token)["result"][0]
            z_id, z_name = zone["id"], zone["name"]
            for sub, path in CONFIGS.items():
                # 判断是读本地文件还是远程 URL
                if os.path.exists(path):
                    with open(path, "r") as f:
                        ips = [l.strip() for l in f if l.strip()]
                else:
                    ips = [l.strip() for l in requests.get(path).text.splitlines() if l.strip()]

                full_name = z_name if sub == "@" else f"{sub}.{z_name}"
                # 删除旧记录
                records = cf_api(f"zones/{z_id}/dns_records?name={full_name}&type=A", token)["result"]
                for r in records:
                    cf_api(f"zones/{z_id}/dns_records/{r['id']}", token, "DELETE")
                # 添加新记录
                for ip in ips:
                    cf_api(f"zones/{z_id}/dns_records", token, "POST", 
                           {"type": "A", "name": full_name, "content": ip, "ttl": 60})
                    print(f"成功: {full_name} -> {ip}")
        except Exception as e:
            print(f"同步失败: {e}")

if __name__ == "__main__":
    main()
