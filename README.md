# SteamAutoCracker Applist Generator

**SteamAutoCracker Applist Generator** is an automated Python tool that continuously fetches and maintains a comprehensive list of Steam applications (games, software, DLC, etc.) with their installation directory names. The tool queries the Steam Web API and Steam client to extract detailed app information and automatically syncs the data to a GitHub repository.

## Features

- **Automated Steam App Discovery**: Continuously fetches Steam's entire app catalog using the official Steam Web API
- **Detailed App Information**: Extracts app IDs, game directory names, and installation directory names for each Steam application
- **Parallel Processing**: Uses multi-threaded workers with gevent for efficient concurrent API queries
- **Resume Capability**: Tracks progress and can resume from the last processed app ID in case of interruption
- **GitHub Integration**: Automatically uploads and updates the app list to a GitHub repository
- **Continuous Updates**: Runs in a loop with configurable intervals to keep the app list up-to-date
- **Robust Error Handling**: Includes retry logic and timeout handling for reliable operation

## Requirements

- Python 3.6 or higher
- Steam Web API Key ([Get one here](https://steamcommunity.com/dev/apikey))
- GitHub Personal Access Token with repository write permissions
- Internet connection

### Python Dependencies

All required Python packages are listed in `requirements.txt`:

```
requests
steam[client]
eventemitter
protobuf>=3.19.0
gevent
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SquashyHydra/SteamAutoCracker.git
   cd SteamAutoCracker
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application** (see Configuration section below)

## Configuration

On first run, the script will create a `config.ini` file with default values. You need to update this file with your credentials:

### config.ini Structure

```ini
[SteamSettings]
key = steam_web_api_key_here

[GithubLogin]
GithubToken = your_github_token
GithubOwner = yourusername
GithubRepo = yourrepo
GithubBranch = main
```

### Configuration Steps

1. **Get a Steam Web API Key**:
   - Visit https://steamcommunity.com/dev/apikey
   - Sign in with your Steam account
   - Register for an API key (domain name can be anything)
   - Copy the key

2. **Create a GitHub Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Give it a name and select the `repo` scope
   - Generate and copy the token

3. **Update config.ini**:
   - Replace `steam_web_api_key_here` with your actual Steam Web API key
   - Replace `your_github_token` with your GitHub Personal Access Token
   - Replace `yourusername` in `GithubOwner` with your GitHub username
   - Replace `yourrepo` in `GithubRepo` with your repository name (just the repo name, not owner/repo)
   - Set the branch name in `GithubBranch` (default is `main`)

## Usage

### Basic Usage

Run the script with continuous updates (default behavior):

```bash
python appid_validator.py
```

This will:
1. Connect to Steam's API and client
2. Fetch all Steam applications
3. Process each app to extract installation directory information
4. Save the data to `applist.txt`
5. Upload the file to your GitHub repository
6. Wait 30 minutes and repeat the process

### Single Run Mode

To perform a single update without continuous looping, modify the main function call in the script:

```python
if __name__ == "__main__":
    main(loop=False)  # Changed from loop=True
```

## How It Works

### Data Collection Process

1. **API Initialization**: The script loads configuration from `config.ini` and authenticates with both Steam Web API and GitHub API

2. **App List Retrieval**: Uses Steam's `IStoreService/GetAppList` endpoint to fetch all available applications
   - Fetches apps in batches
   - Tracks the last processed app ID for resumption
   - Handles pagination automatically

3. **Parallel Processing**: For each app in the list:
   - Creates multiple worker threads (default: 6 concurrent workers)
   - Each worker connects to Steam client anonymously
   - Queries detailed product information using `get_product_info`
   - Extracts:
     - `appid`: Steam application ID
     - `name`: Game directory name (from `extended.gamedir`)
     - `name2`: Installation directory name (from `config.app_mappings.installdir`)
   
4. **Data Storage**: Results are saved to `applist.txt` in Python list format

5. **GitHub Sync**: Automatically uploads/updates the `applist.txt` file to your GitHub repository

6. **Continuous Updates**: Waits 30 minutes before repeating the entire process

### Output Format

The `applist.txt` file contains a Python list of dictionaries:

```python
[
    {'appid': 10, 'name': 'cstrike', 'name2': 'Counter-Strike'},
    {'appid': 40, 'name': 'dmc', 'name2': 'Deathmatch Classic'},
    {'appid': 20, 'name': 'tfc', 'name2': 'Team Fortress Classic'},
    ...
]
```

Where:
- `appid`: The unique Steam application ID
- `name`: The game's internal directory name (gamedir)
- `name2`: The installation directory name (may be None if not available)

## File Structure

```
SteamAutoCracker/
│
├── appid_validator.py      # Main script
├── requirements.txt         # Python dependencies
├── applist.txt             # Generated Steam app list (large file)
├── config.ini              # Configuration file (created on first run)
├── last_appid.txt          # Tracks last processed app ID (temporary)
└── .gitignore              # Git ignore rules
```

### Generated Files

- **config.ini**: Configuration file with API keys and GitHub settings
- **applist.txt**: The main output file containing all Steam apps
- **last_appid.txt**: Temporary file to track progress (auto-deleted after completion)

## Error Handling

The script includes robust error handling:

- **Timeout Protection**: Each app query has a configurable timeout (default: 20 seconds)
- **Automatic Retries**: Failed queries are retried up to 2 times with exponential backoff
- **Connection Management**: Each worker maintains its own Steam client connection
- **Graceful Degradation**: If app details can't be retrieved, basic information is still saved
- **Resume Support**: If interrupted, the script can resume from the last processed app ID

## Performance Notes

- **Processing Time**: Initial complete scan can take several hours depending on Steam's catalog size (~150,000+ apps)
- **Concurrency**: Default is 6 concurrent workers; can be adjusted in the `run_parallel()` function
- **Memory Usage**: The app list can be large (several MB) as it stores all Steam apps
- **API Rate Limits**: The script respects Steam's rate limits through timeout and retry mechanisms

## Troubleshooting

### Common Issues

1. **"Please update the 'key' in the 'SteamSettings' section"**
   - You haven't updated your Steam API key in `config.ini`

2. **"Please update the 'GithubToken' in the 'GithubLogin' section"**
   - You haven't updated your GitHub credentials in `config.ini`

3. **Connection Timeouts**
   - Increase the timeout value in `run_parallel(concurrency=6, timeout=20)`
   - Reduce concurrency if experiencing many timeouts

4. **GitHub Upload Fails**
   - Verify your GitHub token has `repo` permissions
   - Check that the repository name is correct (format: `owner/repo-name`)
   - Ensure the target branch exists

## Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## License

This project is open-source. Please check the repository for license information.

## Disclaimer

This tool is for educational and research purposes. Make sure to comply with:
- [Steam Web API Terms of Use](https://steamcommunity.com/dev/apiterms)
- [GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)

## Author

Developed and maintained by [SquashyHydra](https://github.com/SquashyHydra)

## Acknowledgments

- Uses the [steam](https://github.com/ValvePython/steam) Python library for Steam client interaction
- Built with [gevent](http://www.gevent.org/) for concurrent processing
- Integrates with [GitHub API](https://docs.github.com/en/rest) for automated uploads
