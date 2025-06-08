# Purgearr

**Purgearr** is a Python-based tool that interacts with Sonarr and Radarr APIs to manage and delete media files based on configurable criteria such as file age and tags. This script helps maintain your media library by automatically purging old files that are no longer needed, while allowing you to preserve certain shows or movies using the "keeper" tag.

## Features

- **Automatic Deletion**: Delete media files older than 90 days.
- **Test Mode**: Simulate the deletion process to preview what files would be removed.
- **Intelligent Season-Überwachung**: Deactivates monitoring of fully deleted seasons.
- **Tag Exclusion**: Protect shows and movies tagged with "keeper" from deletion.
- **Customizable**: Set custom cut-offs and/or keeper tags within the script.

## Requirements

- Python 3.8+
- Sonarr and Radarr installations
- API keys for both Sonarr and Radarr

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/h3rb1n4t0r/purgearr.git
   cd purgearr
   ```

2. Install required Python packages:

   ```bash
   pip install requests
   ```

3. Update the `Purgearr.py` script with your Sonarr and Radarr API keys and URLs:

   ```python
   SONARR_API_KEY = 'your_sonarr_api_key'
   RADARR_API_KEY = 'your_radarr_api_key'
   SONARR_URL = 'http://sonarr.yourdomain.com:8989/api/v3'
   RADARR_URL = 'http://radarr.yourdomain.com:7878/api/v3'
   ```

## Usage

### Test Mode

Run the script in **test mode** to preview which files would be deleted without making any actual changes:

```bash
python3 Purgearr.py --test
```

### Actual Deletion

Run the script to permanently delete files older than 90 days:

```bash
python3 Purgearr.py
```

### Automating with Cronjob

To automate the execution of Purgearr, you can set up a cronjob that runs the script at a specific time interval. Here's how to do it:

1. Open the crontab editor:

   ```bash
   crontab -e
   ```

2. Add a cronjob entry to run Purgearr daily at midnight (00:00). Modify the path to the script based on its location on your system:

   ```bash
   0 0 * * * /usr/bin/python3 /path/to/Purgearr.py >> /path/to/log/purgearr.log 2>&1
   ```

   This cronjob does the following:
   - Runs the script every day at midnight (00:00).
   - Logs both standard output and errors to `purgearr.log` for troubleshooting and monitoring.

3. Save and exit the crontab editor.

**Notes:**
- Make sure to set the correct path to the Python binary and the script.
- Check the log file periodically to ensure the script runs as expected.

## Tag Exclusion

Purgearr supports excluding media from deletion by using tags. If a show or movie is tagged with `keeper`, the file will be skipped.

You can add the "keeper" tag in Sonarr or Radarr:

1. Go to the series/movie page.
2. Navigate to the tags section.
3. Add or create the tag "keeper".

## Configuration

- The script is set to delete files older than 90 days. You can adjust this by changing the `cutoff_date` value in the script.
- The default tag for exclusion is `"keeper"`. To modify this, update the `EXCLUDE_TAG` variable in the script.

```python
EXCLUDE_TAG = 'keeper'
```

## Contributing

If you find a bug or have suggestions for improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the GNU General Public License v3.0.

Under the GPL, you are free to use, modify, and distribute this software, provided that any derivative works are also distributed under the same license.
