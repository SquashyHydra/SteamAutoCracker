from steam.client import SteamClient
import vdf
import time

client = SteamClient()

@client.on('connected')
def on_connected():
    client.login(
        username='bot', password='botpass')  # or use login_key
    
@client.on('logged_on')
def on_logged_on():
    print('logged in, requesting product info for appid 570')
    # Many Python Steam client libs expose a get_product_info or PICS wrapper.
    # If your library exposes "get_product_info" do something like:
    client.get_product_info([570], callback=on_product_info)  # API name can vary

def on_product_info(result):
    # result will contain KeyValue-like data; if it's raw VDF, parse with python-vdf
    # Example: if result.kv is a string VDF:
    kv = vdf.loads(result.kv_text)  # or result.kv if already parsed
    # Look for installdir in common or depots
    if 'common' in kv and 'installdir' in kv['common']:
        print('common.installdir =', kv['common']['installdir'])
    if 'depots' in kv:
        for depot_id, depot_info in kv['depots'].items():
            if 'installdir' in depot_info:
                print('depot', depot_id, 'installdir =', depot_info['installdir'])

client.connect()
while True:
    client.run_forever()  # or the appropriate event loop pump for your library
    time.sleep(1)