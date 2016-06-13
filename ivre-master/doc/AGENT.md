# Introduction #

[IVRE](README.md) agent is meant to be run in an environment not
totally controlled (e.g., during a pentest, on a machine you have just
owned and want to use to do some network recon without installing
IVRE).

IVRE agent only requires nmap (of course), screen and rsync (plus
`/bin/sh` and basic shell utils, including `grep`).

# Installation #

On the "master", install IVRE following the instructions of the
[INSTALL](INSTALL.md) file. Install also `screen`.

On the "slave(s)", the `agent` script must be deployed, together with
`nmap`, `screen` and `rsync`.

# Run

## On the slave(s) ##

The computer running IVRE (the "master") needs to be able to access
via `rsync` the data directory of the agents (to add targets and to
retrieve results): this is not an issue if you are running the agent
and IVRE itself on the same machine. If you are running IVRE and the
agent on two different hosts (and, except for simple or testing
configurations, you should do that), you have to run `sshd` or
`rsyncd` on the agent host, or share the agent files (using NFS, SMB
or whatever the IVRE side can mount).

First, `mkdir` & `cd` to the directory you want to use as your agent
data directory.

Make sure the needed binaries are in the `PATH` environment variable
(including `nmap` and `screen`), adapt if needed the variables at the
beginning of the script, particularly `NMAPOPTS`, `NMAPSCRIPTS` and
`THREADS`.

Values for `NMAPOPTS` and `NMAPSCRIPTS` cause scans similar to those
run by `ivre runscans` by default (with IVRE's default template). To
get options from other templates, run `ivre runscans --nmap-template
aggressive` (for example) and copy the corresponding values in the
`agent` script.

Then just run the `agent` script.

The script will start `screen`, and you can just detach by using (if
you have the default key bindings): `C-a d`.

When the scan is over, to stop the agent, reattach the screen session
by running `screen -r`, and type `C-c` as many times as needed to kill
all the instances of the script and get back to your shell.

Please refer to `screen` documentation if you need.

## On the master ##

You need to make sure the user running `ivre runscansagent` or `ivre
runscansagentdb` on the "master" can access (without password) to the
agents data directories.

When the agents are all ready, you have two options, using `ivre
runscansagent` or `ivre runscansagentdb`. In both cases, scan options
are the same than with `ivre runscans`.

The first one (`ivre runscansagent`) is the "old-school" version: it
will not allow to dynamically add or remove agents, and will fetch the
results under `./agentsdata/output` directory, you have to import the
results by yourself.

On the other hand, the second one (`ivre runscansagentdb`) will use
the DB to manage the agents, but is still experimental.

### `ivre runscansagent`, the "old-school" one ###

You have to specify the agent(s) data directory. For example, run:

    $ ivre runscansagent --routable --limit 1000 \
    >     agenthost1:/path/to/agent/dir      \
    >     agenthost2:/path/to/agent/dir      \

You can now import the results as if you had run the "regular" `ivre
runscans` program to scan locally, see [README](README.md). The
results are stored under `agentsdata/output/`

### `ivre runscansagentdb`, the "modern" (but probably broken) one ###

Please note that it is important to run all the `ivre
runscansagentdb` from the same host (the "master", which does not
need to be the same host than the database server), since it relies on
local directories.

First, let's create a master and add the agent(s):

    $ ivre runscansagentdb --add-local-master
    $ ivre runscansagentdb --source MySource --add-agent \
    >     agenthost1:/path/to/agent/dir \
    >     agenthost2:/path/to/agent/dir

Let's check it's OK:

    $ ivre runscansagentdb --list-agents
    agent:
      - id: 543bfc8a312f915728f1709b
      - source name: MySource
      - remote host: agenthost1
      - remote path: /path/to/agent/dir/
      - local path: /var/lib/ivre/master/sbOist
      - rsync command: rsync
      - current scan: None
      - currently synced: True
      - max waiting targets: 60
      - waiting targets: 0
      - can receive: 60
    agent:
      - id: 543bfc8a312f915728f1709c
      - source name: MySource
      - remote host: agenthost2
      - remote path: /path/to/agent/dir/
      - local path: /var/lib/ivre/master/m2584z
      - rsync command: rsync
      - current scan: None
      - currently synced: True
      - max waiting targets: 60
      - waiting targets: 0
      - can receive: 60

Now we can add a scan, and assign the (available) agents to that scan:

    $ ivre runscansagentdb --assign-free-agents --routable --limit 1000

And see if it works:

    $ ivre runscansagentdb --list-scans
    scan:
      - id: 543bfcbf312f9158d6caeadf
      - categories:
        - ROUTABLE
      - targets added: 0
      - results fetched: 0
      - total targets to add: 1000
      - available targets: 2712693508
      - internal state: (2174385484, 551641673, 387527645, 0)
      - agents:
        - 543bfc8a312f915728f1709b
        - 543bfc8a312f915728f1709c

For now, nothing has been sent to the agents. To really start the
process, run:

    $ ivre runscansagentdb --daemon

After some time, the first results get imported in the database
(`READING [...]`, `HOST STORED: [...]`, `SCAN STORED: [...]`). You can
stop the daemon at any time by `(p)kill`-ing it (using `CTRL+c` will
do).

When all the targets have been sent to an agent, the agents get
disassociated from the scan so that another scan can use them. You can
check the scan evolution by issuing `ivre runscansagentdb
--list-scans`.


---

This file is part of IVRE. Copyright 2011 - 2015
[Pierre LALET](mailto:pierre.lalet@cea.fr)