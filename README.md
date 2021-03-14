# GDScan

Generate a report in CSV format summarizing all shared items in a Google Drive account

## Installation (macOS)

You'll need a [Python 3.x][python] interpreter (including [pip][pip]) to run the GDScan script. My recommendation on macOS is to use [Homebrew][homebrew] using the instructions listed below.

### Install Homebrew

Follow the [Homebrew installation instructions][homebrew-installation].

### Install Python and Git

Once you have Homebrew, open a terminal and run the following commands to install Python and [Git][git]:

```bash
brew install git python
```

### Clone project

From a terminal:

```bash
cd $HOME
git clone https://github.com/rcook/gdscan.git
$HOME/gdscan/setup
```

### Show script help

This will run the script and display its command-line help:

```bash
$HOME/gdscan/gdscan.py --help
```

This will display help like the following:

```
usage: gdscan.py [-h] [--client-secrets-path CLIENTSECRETSPATH] [--item-limit ITEMLIMIT] [--config-dir CONFIGDIR] [--overwrite] OUTPUTPATH

positional arguments:
  OUTPUTPATH            Path to output CSV file to be generated

optional arguments:
  -h, --help            show this help message and exit
  --client-secrets-path CLIENTSECRETSPATH, -s CLIENTSECRETSPATH
                        Path to Google Drive client secrets/client ID file
  --item-limit ITEMLIMIT, -n ITEMLIMIT
                        limit scan to fixed number of shared items (default: (none))
  --config-dir CONFIGDIR, -c CONFIGDIR
                        path to configuration directory (default: $HOME/gdscan)
  --overwrite, -f       force overwrite of output CSV file if it already exists
```

### Obtain Google Drive API client secret

Follow the [Google Drive API][google-drive-api-auth] instructions to obtain a client secrets file (also known as client ID file) to allow GDScan to connect to your Google Drive account. Save this file in your home directory with the file name `client_id.json`.

### Script examples

Generate full report describing all the shared items in your Google Drive account:

```bash
$HOME/gdscan/gdscan.py report.csv
```

Test that script works by generating report for first five shared items in your Google Drive account:

```bash
$HOME/gdscan/gdscan.py --item-limit 5 test.csv
```

## Inspiration

This project is inspired by [google-drive-list-shared][google-drive-list-shared] by [James W. Thorne][james-w-thorne] and his article [_Find All Shared Files in Google Drive with a Python Script_][thorne-article].

## Licence

[MIT License][licence]

[git]: https://git-scm.com/
[google-drive-list-shared]: https://github.com/jameswthorne/google-drive-list-shared
[google-drive-api-auth]: https://developers.google.com/drive/api/v3/about-auth
[homebrew]: https://brew.sh/
[homebrew-installation]: https://docs.brew.sh/Installation
[james-w-thorne]: https://github.com/jameswthorne/
[licence]: LICENSE
[pip]: https://pypi.org/project/pip/
[python]: https://www.python.org/
[thorne-article]: https://thornelabs.blog/posts/find-all-shared-files-in-google-drive-with-a-python-script.html
