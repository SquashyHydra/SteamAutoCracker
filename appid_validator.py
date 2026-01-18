import ast
import base64
import requests
import json
import bs4

config_file = "config.ini"

default_SteamLogin = {
    'sessionid': 'your_sessionid',
    'steamLoginSecure': 'your_steamLoginSecure',
}

default_GithubLogin = {
    'GithubToken': 'your_github_token',
    'GithubOwner': 'yourusername',
    'GithubRepo': 'yourusername/yourrepo',
    'GithubBranch': 'main',
}

def create_config(config_file="config.ini"):
    config = {}
    config['SteamLogin'] = default_SteamLogin
    config['GithubLogin'] = default_GithubLogin
    with open(config_file, 'w') as configfile:
        configfile.write(json.dumps(config, indent=4))

def load_config(config_file="config.ini"):
    config = {}
    try:
        with open(config_file, 'r') as configfile:
            configfile_content = json.loads(configfile.read())

        config['SteamLogin'] = configfile_content.get('SteamLogin', {})
        config['GithubLogin'] = configfile_content.get('GithubLogin', {})
    except (FileNotFoundError, json.JSONDecodeError):
        create_config()
        config = load_config(config_file)

    for key, _ in default_SteamLogin.items():
        if config['SteamLogin'][key] == default_SteamLogin[key]:
            print(f"Please update the '{key}' in the 'SteamLogin' section of {config_file}.")
            exit(1)
    for key, _ in default_GithubLogin.items():
        if config['GithubLogin'][key] == default_GithubLogin[key]:
            print(f"Please update the '{key}' in the 'GithubLogin' section of {config_file}.")
            exit(1)
    return config

config = load_config()

cookies = {
    'birthtime': '1044482401',
    'lastagecheckage': '6-February-2003',
    'sessionid': config['SteamLogin']['sessionid'],
    'steamLoginSecure': config['SteamLogin']['steamLoginSecure']
}

gh_token = config['GithubLogin']['GithubToken']
gh_owner = config['GithubLogin']['GithubOwner']
gh_repo = config['GithubLogin']['GithubRepo']
gh_branch = config['GithubLogin']['GithubBranch']

def get_apphub_appname(appID):
    url = f"https://store.steampowered.com/app/{appID}"
    try:
        response = requests.get(url, cookies=cookies)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        app_name_tag = soup.find('div', class_='apphub_AppName')
        if app_name_tag:
            return app_name_tag.text.strip()
        else:
            return None
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    
# check if appID is DLC or Soundtrack
def is_downloadable_content(appID):
    url = f"https://store.steampowered.com/app/{appID}"
    is_dlc = False
    is_soundtrack = False
    try:
        response = requests.get(url, cookies=cookies)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        details = soup.find_all('div', class_='game_area_bubble game_area_dlc_bubble')
        for detail in details:
            h1_tag = detail.find('h1')
            if h1_tag:
                if 'Downloadable Content' in h1_tag.text:
                    is_dlc = True
        
        details = soup.find_all('div', class_='game_area_bubble game_area_soundtrack_bubble')
        for detail in details:
            h1_tag = detail.find('h1')
            if h1_tag:
                if 'Downloadable Soundtrack' in h1_tag.text:
                    is_soundtrack = True

        if is_dlc or is_soundtrack:
            return True
        else:
            return False
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return False     

# function to check if page returns with a 302 status code
def is_redirect(appID):
    url = f"https://store.steampowered.com/app/{appID}"
    try:
        response = requests.get(url, allow_redirects=False, cookies=cookies)
        if response.status_code == 302:
            return False
        elif response.status_code == 200:
            return True
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return False
    
# save last tested appID to a file
def save_last_tested_appID(appID, filename="last_tested_appID.txt"):
    try:
        with open(filename, "w") as file:
            file.write(str(appID))
    except IOError as e:
        print(f"An error occurred while saving the appID: {e}")

# load last tested appID from a file
def load_last_tested_appID(filename="last_tested_appID.txt"):
    try:
        with open(filename, "r") as file:
            num = int(file.read().strip()) + 1
            if num > 4294967295:
                return 0
            return num
    except (IOError, ValueError):
        return 0

# save a list of valid appIDs to a file without overwriting existing content
def save_valid_appIDs(appIDs:list, existing_appIDs:list, filename="applist.txt"):
    try:
        print("Saving valid appIDs...")
        already_saved_appIDs = []
        for app in existing_appIDs:
            already_saved_appIDs.append(app["appid"])
        valid_appIDs = []
        try:
            for appID in appIDs:
                if appID not in already_saved_appIDs:
                    appid_json = {
                        "appid": appID,
                        "name": get_apphub_appname(appID)
                    }
                    valid_appIDs.append(appid_json)
            with open(filename, "a", encoding="utf-8") as file:
                file.write(f"{valid_appIDs}")
        except IOError as e:
            print(f"An error occurred while saving valid appIDs: {e}")

        # upload to github
        upload_to_github()
    except KeyboardInterrupt:
        pass

def load_valid_appIDs(filename="applist.txt"):
    print("Loading existing valid appIDs...")
    valid_appIDs = []
    try:
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                appIDs = line
        appIDs = ast.literal_eval(appIDs)
        for app in appIDs:
            valid_appIDs.append(app["appid"])
    except IOError:
        pass
    except KeyboardInterrupt:
        print("Process interrupted by user.")
        exit(1)
    return valid_appIDs, appIDs

# upload generated applist.txt to github repository
def upload_to_github(filename="applist.txt"):
    print("Uploading applist.txt to GitHub...")
    try:
        path = f"{filename}"
        message = f"Add/Update {filename} automatically via script"
        
        with open(filename, "rb") as f:
            data = f.read()
        b64content = base64.b64encode(data).decode()

        url = f"https://api.github.com/repos/{gh_owner}/{gh_repo}/contents/{path}"
        headers = {
            "Authorization": f"Bearer {gh_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        params = {"ref": gh_branch}
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 200:
            existing = r.json()
            sha = existing["sha"]
        else:
            sha = None

        payload = {
            "message": message,
            "content": b64content,
            "branch": gh_branch,
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

# main loop to test appIDs
def main(end_appID=4294967295):
    valid_appIDs, appIDs = load_valid_appIDs()
    start_appID = load_last_tested_appID()
    curr_appID = start_appID
    try:
        while True:
            for appID in range(start_appID, end_appID + 1):
                if appID not in valid_appIDs:
                    if is_redirect(appID):
                        if not is_downloadable_content(appID):
                            print(f"Valid appID found: {appID}")
                            valid_appIDs.append(appID)
                else:
                    print(f"Skipping already validated appID: {appID}")
                save_last_tested_appID(appID)
                curr_appID = appID
            if curr_appID >= end_appID:
                print("Reached the end of the appID range. Restarting from 0.")
                save_valid_appIDs(valid_appIDs, appIDs)
                start_appID = 0
    except KeyboardInterrupt:
        print("Process interrupted by user. Saving progress...")
        save_last_tested_appID(curr_appID)
    save_valid_appIDs(valid_appIDs, appIDs)

if __name__ == "__main__":
    main()