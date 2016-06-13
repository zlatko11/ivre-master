#! /usr/bin/env python

# This file is part of IVRE.
# Copyright 2011 - 2014 Pierre LALET <pierre.lalet@cea.fr>
#
# IVRE is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IVRE is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IVRE. If not, see <http://www.gnu.org/licenses/>.

import ivre.target
import ivre.utils
import ivre.scanengine

import os
import sys
import subprocess

MAINDIR = "./agentsdata"

ACTION_SYNC = 1
ACTION_FEED = 2
ACTION_BOTH = 3

def main():
    try:
        import argparse
        parser = argparse.ArgumentParser(
            description='Sends targets to a remote agent.',
            parents=[ivre.target.argparser])
        USING_ARGPARSE = True
    except ImportError:
        import optparse
        parser = optparse.OptionParser(
            description='Sends targets to a remote agent.',
            usage='Usage: ivre runscansagent [options] AGENT [AGENT ...]')
        for args, kargs in ivre.target.argparser.args:
            parser.add_option(*args, **kargs)
        parser.parse_args_orig = parser.parse_args

        def parse_args():
            args, agents = parser.parse_args_orig()
            args._update_loose({'agents': agents})
            return args
        parser.parse_args = parse_args
        parser.add_argument = parser.add_option
        USING_ARGPARSE = False
    parser.add_argument('--category', metavar='CAT', default="MISC",
                        help='tag scan results with this category')
    parser.add_argument('--max-waiting', metavar='TIME', type=int, default=60,
                        help='maximum targets waiting')
    parser.add_argument('--sync', dest='action', action='store_const',
                        const=ACTION_SYNC, default=ACTION_BOTH)
    parser.add_argument('--dont-store-down', dest='storedown',
                        action='store_const',
                        const=False, default=True)
    parser.add_argument('--feed', dest='action', action='store_const',
                        const=ACTION_FEED)
    if USING_ARGPARSE:
        parser.add_argument('agents', metavar='AGENT', nargs='+',
                            help='agents to use (rsync address)')
    args = parser.parse_args()
    if args.categories is None:
        args.categories = [args.category]
    elif args.category not in args.categories:
        args.categories.append(args.category)
    agents = [
        ivre.scanengine.Agent.from_string(a, localbase=MAINDIR,
                                          maxwaiting=args.max_waiting)
        for a in args.agents
    ]
    for a in agents:
        a.create_local_dirs()
    if args.action == ACTION_SYNC:
        camp = ivre.scanengine.Campaign([], args.category, agents,
                                        os.path.join(MAINDIR, 'output'),
                                        visiblecategory='MISC',
                                        storedown=args.storedown)
        ivre.scanengine.syncloop(agents)
    elif args.action in [ACTION_FEED, ACTION_BOTH]:
        if args.action == ACTION_BOTH:
            # we make sure we're in screen
            if os.environ['TERM'] != 'screen':
                subprocess.call(['screen'] + sys.argv)
                sys.exit(0)
            # we run the sync process in another screen window
            subprocess.call(['screen'] + sys.argv + ['--sync'])
        targets = ivre.target.target_from_args(args)
        if targets is None:
            parser.error(
                'one argument of --country/--asnum/--range/--network/'
                '--routable/--file/--test is required'
            )
        camp = ivre.scanengine.Campaign(targets, args.category, agents,
                                        os.path.join(MAINDIR, 'output'),
                                        visiblecategory='MISC')
        try:
            camp.feedloop()
        except KeyboardInterrupt:
            sys.stderr.write('Stop feeding.\n')
            sys.stderr.write('Use "--state %s" to resume.\n' %
                             ' '.join(map(str, camp.targiter.getstate())))
        except Exception as e:
            sys.stderr.write('ERROR: %r.\n' % e)
            sys.stderr.write('Use "--state %s" to resume.\n' %
                             ' '.join(map(str, camp.targiter.getstate())))
        else:
            sys.stderr.write('No more targets to feed.\n')
            if os.environ['TERM'] != 'screen':
                sys.stderr.write('Press enter to exit.\n')
                raw_input()
        raw_input()
