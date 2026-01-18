import requests
import ast
import configparser
import base64
import os
import time

last_appid="last_appid.txt"
steam_applist="applist.txt"
config_file="config.ini"

default_SteamSettings = {
    'key': 'steam_web_api_key_here',
}

default_GithubLogin = {
    'GithubToken': 'your_github_token',
    'GithubOwner': 'yourusername',
    'GithubRepo': 'yourusername/yourrepo',
    'GithubBranch': 'main',
}

def create_config(filename=config_file):
    config = configparser.ConfigParser()
    config['SteamSettings'] = default_SteamSettings
    config['GithubLogin'] = default_GithubLogin
    with open(filename, 'w') as configfile:
        config.write(configfile)

def load_config(filename=config_file):
    config = configparser.ConfigParser()
    try:
        config.read(filename)
        steam_settings = config['SteamSettings']
        github_login = config['GithubLogin']
    except (KeyError, configparser.Error):
        create_config()
        return load_config()

    for key, _ in default_SteamSettings.items():
        if steam_settings.get(key) == default_SteamSettings[key]:
            print(f"Please update the '{key}' in the 'SteamSettings' section of config.ini.")
            exit(1)
    for key, _ in default_GithubLogin.items():
        if github_login.get(key) == default_GithubLogin[key]:
            print(f"Please update the '{key}' in the 'GithubLogin' section of config.ini.")
            exit(1)

    return {
        'SteamSettings': steam_settings,
        'GithubLogin': github_login
    }

config = load_config()

def save_last_appid(appid, filename=last_appid):
    try:
        with open(filename, 'w') as f:
            f.write(str(appid))
    except IOError as e:
        print(f"An error occurred while saving the last appid: {e}")

def load_last_appid(filename=last_appid):
    try:
        with open(filename, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None

def get_steam_app_list(last_appid=None):
    base_url = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
    
    if last_appid:
        print(f"Fetching app list from last_appid: {last_appid}...")
        params = f"key={config['SteamSettings']['key']}&last_appid={last_appid}"
    else:
        print("Fetching app list from the beginning...")
        params = f"key={config['SteamSettings']['key']}"

    url = f'{base_url}?{params}'

    response = requests.get(url)
    
    if response.status_code == 200:
        response_json = response.json()['response']
    
    if response_json:
        data = response_json['apps']
        try:
            more_data = response_json['have_more_results']
        except KeyError:
            more_data = False
        try:
            last_appid = response_json['last_appid']
            save_last_appid(last_appid)
        except KeyError:
            last_appid = None
    
    print(f"Fetched {len(data)} apps - last used appid: {last_appid} - {"Yes" if more_data else "No"} there are {"More" if more_data else "No more"} results.")
    return data, more_data, last_appid

def save_to_file(data, filename=steam_applist):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(str(data))
    
    upload_to_github()

def load_from_file(filename=steam_applist):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = ast.literal_eval(f.read())
    except FileNotFoundError:
        data = []
    return data

def update_list(existing_list, new_list):
    print("Updating existing app list with new data...")
    existing_appids = {app['appid'] for app in existing_list if 'appid' in app}
    to_add = []
    seen = existing_appids
    append = to_add.append
    for app in new_list:
        appid = app.get('appid')
        if appid and appid not in seen:
            if appid not in existing_appids:
                seen.add(appid)
                append(app)
    existing_list.extend(to_add)
    return existing_list

def remove_last_appid_file(filename=last_appid):
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass

# upload generated applist.txt to github repository
def upload_to_github(filename=steam_applist):
    print("Uploading applist.txt to GitHub...")
    try:
        path = f"{filename}"
        message = f"Add/Update {filename} automatically via script"
        
        with open(filename, "rb") as f:
            data = f.read()
        b64content = base64.b64encode(data).decode()

        url = f"https://api.github.com/repos/{config['GithubLogin']['GithubOwner']}/{config['GithubLogin']['GithubRepo']}/contents/{path}"
        headers = {
            "Authorization": f"Bearer {config['GithubLogin']['GithubToken']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        params = {"ref": config['GithubLogin']['GithubBranch']}
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 200:
            existing = r.json()
            sha = existing["sha"]
        else:
            sha = None

        payload = {
            "message": message,
            "content": b64content,
            "branch": config['GithubLogin']['GithubBranch'],
        }
        if sha:
            payload["sha"] = sha

        resp = requests.put(url, headers=headers, json=payload)
        resp.raise_for_status()
        print("Success:", resp.json()["commit"]["sha"])
    except requests.RequestException as e:
        print(f"An error occurred while uploading to GitHub: {e}")
    except KeyboardInterrupt:
        pass

def run():
    applist = load_from_file()
    last_appid = load_last_appid()
    while True:
        if last_appid:
            data, more_data, last_appid = get_steam_app_list(last_appid)
        else:
            data, more_data, last_appid = get_steam_app_list()

        applist = update_list(applist, data)

        if not more_data or not last_appid:
            break

    return applist

def main():
    while True:
        applist = run()
        save_to_file(applist)
        remove_last_appid_file()
        print("Waiting for 30 minutes before next update...")
        time.sleep(30 * 60)

if __name__ == "__main__":
    main()