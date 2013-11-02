robotgame
=========

Fork of http://robotgame.org/rules

### Install

```
mkdir -p ~/git
cd ~/git
test -d robotgame || git clone git@github.com:gwillem/robotgame.git
cd robotgame
sudo pip install restrictedpython
sudo apt-get install python-tk
```

### Run

```
# to let samplebot compete against itself
python run.py bots/samplebot.py bots/samplebot.py maps/default.py --render
```

