# SCP-079-RECHECK

This bot is used to recheck NSFW media messages.

## How to use

- See the [manual](https://telegra.ph/SCP-079-RECHECK-12-04)
- See [this article](https://scp-079.org/recheck/) to build a bot by yourself
- Discuss [group](https://t.me/SCP_079_CHAT)

## To Do List

- [x] Auto delete NSFW media messages
- [x] Update user's score
- [x] Watch ban or ban by checking user's score and status

## Requirements

- Python 3.6 or higher
- Debian 10: `sudo apt install libatlas-base-dev libblas-dev libhdf5-dev liblapack-dev opencc -y`
- Install anacodna3 to `~/scp-079/conda`
- `conda`: `conda create --name recheck tensorflow=1.15.0`
- `conda`: `conda activate recheck`
- `pip`: `pip install -r requirements.txt` or `pip install -U APScheduler emoji keras==2.2.5 OpenCC Pillow pyAesCrypt pyrogram[fast] tensorflow==1.15.0`

```bash
mkdir -p ~/scp-079/recheck/models
cd ~/scp-079/recheck/models
git clone https://github.com/rockyzhengwu/nsfw.git nsfw
git clone https://github.com/GantMan/nsfw_model.git temp
mv temp/nsfw_detector nsfw_detector
rm -r temp
cd nsfw_detector
wget https://s3.amazonaws.com/nsfwdetector/nsfw.299x299.h5
```

## Files

- plugins
    - functions
        - `channel.py` : Functions about channel
        - `etc.py` : Miscellaneous
        - `file.py` : Save files
        - `filters.py` : Some filters
        - `group.py` : Functions about group
        - `ids.py` : Modify id lists
        - `image.py` : Functions about image
        - `receive.py` : Receive data from exchange channel
        - `telegram.py` : Some telegram functions
        - `tests.py` : Some test functions
        - `timers.py` : Timer functions
        - `user.py` : Functions about user
    - handlers
        - `command.py` : Handle commands
        - `message.py`: Handle messages
    - models
        - `nsfw` : [rockyzhengwu/nsfw](https://github.com/rockyzhengwu/nsfw)
        - `nsfw_detector` : [GantMan/nsfw_model](https://github.com/GantMan/nsfw_model)
    - `glovar.py` : Global variables
- `.gitignore` : Ignore
- `config.ini.example` -> `config.ini` : Configuration
- `LICENSE` : GPLv3
- `main.py` : Start here
- `README.md` : This file
- `requirements.txt` : Managed by pip

## Contribute

Welcome to make this project even better. You can submit merge requests, or report issues.

## License

Licensed under the terms of the [GNU General Public License v3](LICENSE).
