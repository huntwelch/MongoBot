<img src="http://mongobot.com/static/img/mongobot.png" width="150" height="150" />

IRC bot for people who like to muck with IRC bots
-------------------------------------------------

This is a map of the codebase, sort of: http://mongobot.com/static/img/mongomap2.pdf


Getting Started
---------------

There's kind of a bootstrap.sh file that might work if you're on a Mac. No
guarantees.

```
mkvirtualenv MongoBot
pip install -r requirements.txt
```

To run bot: `python medulla.py`

To run bot persistently so it will recover from crashes: `python doctor.py`

You'll need to install MongoDB to use most of the features relating to people. I apologize for this.

The master development branch is the skynet branch. There is a reason.


Dafuq is going on?
------------------

For best results in answering this question, read through medulla.py and cortex.py. 
The comments are... lengthy. Also, learn python. 


Advanced Usage
--------------

MongoBot is capable of running a number of web services and apis. For best
results, run an nginx server and uwsgi server/deploy.ini. And by best results,
I mean any. More documentation on this once I figure out how I did it the 
first time.

Also, the markov functionality is based on redis, so you'll have to get a 
redis server up and running.


Secret settings
---------------

You will need to create a file in the config folder called secrets.yaml.
sample.secrets.yaml has descriptions of each setting, just copy it to
secrets.yaml and set away.


New features
------------

To create a new command in an existing brainmeat category, add the
function to the class and add the decorator @axon. To add a help entry
for the function, add @help("Help message.")

To create a new command category, run this from the root directory: 

    python newbrains.py category_name

This will create a file called category_name.py in brainmeats, with
a class Category_name. Loading of this class will be automated, no
other files need to be altered.

IMPORTANT: new brainmeats won't be enabled for use until they're
added to config/plugins.yaml.


Using ze bot
------------

If you actually manage to get this guy up and running, the default
command characters are '.' for a command, and ':' for running multiple
inputs to a command, so

    .q AAPL

... gets you a stock quote for Apple, and 

    :q AAPL NFLX TWTR

... gets you quotes for Apple, Netflix, and Twitter.

When using in the chat room, you can pipe commands, i.e.:

    .babble Zaphod | .tweet

... will tweet whatever babble spits out.

Why would anyone add piping to a chat bot? I dunno. Things got out of hand.

IMPORTANT: whoever is running the bot instance will have to use
```.adduser``` to add other users. After that they can authorize themselves.


Philosophies
------------

Don't nest logic when you can short circuit.

BAD:

```python
if blah:
    for x in stuff:
        do stuff
```

GOOD:

```python
if not blah: return

for x in stuff:
    do stuff
```

Try to stick to single quotes wherever possible.

String interpolation is better than adding up strings. I'm totally 
not great at remembering this, but I'm trying.

If you want a function to be pipeable to other functions, return the output
instead of just chatting from the function. 

All commit messages for commits touching zalgo code must be 'ZALGO' or 'HE COMES',
otherwise the pull request will be refused.


To Do
-----

* Probably make this readme better
* acro game is broken
* turing.py function names need to be better, this is fucking mandarin
* some odd bugs in channeling
* remove image after thumbnailing, clear all out on boot
* remove video downloads on reboot
* create bootstrap install
* Add autostart for server, if components in place
* add tweet at in twitting
* reddit command breaks without specified subreddit
* Clean up broca
* link holdem to db, make persistant, open up sit/in/out functionality
* finish holdem, needs testing and split pots probably don't work
* also, holdem is just totally broken right now
* stock game: account for splits and reverse splits
* add @requires decorator, check for server, redis, mongo, etc.
* just take out image relink, make it a thumblink
* mud-style game
* interbot com
* streamline web stuff
* multi-platform
* futher abstract thalamus to load an interface depending on connection type
