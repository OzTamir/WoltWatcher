# WoltWatcher
 A dockerized telegram bot to monitor Wolt restaurant and notify when they can take orders again.

## How to use
0. Get your Telegram token and add it in config.json
1. Clone the repository locally:
```bash
git clone https://github.com/OzTamir/WoltWatcher.git
```
2. Edit the config.json file with a telegram token
3. Build the Docker image from the directory:
```bash
docker build --tag wolt-watcher-bot:1.0 .
```
4. Run the continer:
```bash
docker run --detach --name wolt-watcher wolt-watcher-bot:1.0
```
5. Enjoy!
