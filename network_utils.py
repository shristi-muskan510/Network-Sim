def is_valid_ipv4(ip_str):
    """
    [Validation Logic] Check karta hai ki string ek sahi IPv4 address hai ya nahi.
    Jaise '192.168.1.5' is Valid, '256.0.0.1' is Invalid.
    """
    try:
        parts = ip_str.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            val = int(part)
            if val < 0 or val > 255:
                return False
        return True
    except (ValueError, AttributeError):
        return False

def get_network_address(ip, mask):
    """
    [Bonus/Helper] IP aur Mask lekar Network ID nikalta hai.
    Static routing table validation mein kaam aayega.
    """
    if not is_valid_ipv4(ip) or not is_valid_ipv4(mask):
        return None
    ip_parts = list(map(int, ip.split('.')))
    mask_parts = list(map(int, mask.split('.')))
    net_parts = [str(ip_parts[i] & mask_parts[i]) for i in range(4)]
    return ".".join(net_parts)