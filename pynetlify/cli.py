# PyNetlify - Python client and library to interact with Netlify API.
# Copyright (C) 2019  Toni Sissala
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import os
import time
import logging
import argparse
import configparser
from pynetlify import pynetlify


running_python2 = sys.version_info[0] == 2

POLL_DEPLOYS_SLEEP = 2
POLL_DEPLOYS_COUNT = 5


def deploy_folder(netlify_api, args):
    site = netlify_api.get_site(args.site_id)
    deploy_id = netlify_api.deploy_folder_to_site(
        args.folder,
        site)
    if deploy_id is None:
        print('Nothing to deploy')
        return
    nof_poll_deploys = POLL_DEPLOYS_COUNT
    site_live = False
    print('Polling to see when deploy is live')
    while nof_poll_deploys:
        if not running_python2:
            print('.', end='', flush=True)
        deploy = netlify_api.get_deploy(deploy_id)
        if deploy['state'] == 'ready':
            site_live = True
            break
        nof_poll_deploys -= 1
        time.sleep(2)
    msg = 'Site deployed and live at {}'.format(site.url) if site_live else 'Site deployed but not live'
    print(msg)


def create_site(netlify_api, args):
    site_properties = {}
    if args.name:
        site_properties.update({'name': args.name})
    if args.domain:
        site_properties.update({'custom_domain': args.domain})
    site = netlify_api.create_site(site_properties)
    print(site)


def get_site(netlify_api, args):
    site = netlify_api.get_site(args.site_id_or_domain)
    print(site)


def get_site_files(netlify_api, args):
    site = netlify_api.get_site(args.site_id)
    for site_file in netlify_api.get_site_files(site):
        print(site_file)


def list_sites(netlify_api, args):
    for site in netlify_api.sites():
        print(site)


def delete_site(netlify_api, args):
    netlify_api.delete_site(pynetlify.Site(
        name=None, url=None,
        id=args.site_id))


def delete_all_sites(netlify_api, args):
    for site in netlify_api.sites():
        netlify_api.delete_site(site)


def cli_main():
    # DECLARE PARSERS
    # ###############
    argparser = argparse.ArgumentParser(
        description='Interact with Netlify API.')
    subparsers = argparser.add_subparsers(help='action help', dest='action')
    subparsers.required = True
    argparser.add_argument('--auth-token', type=str,
                           help='Netlify Authentication Token')
    argparser.add_argument('--loglevel', default='INFO', choices=[
        'DEBUG', 'INFO', 'WARN', 'ERROR'])
    available_actions = {'create_site': create_site,
                         'get_site': get_site,
                         'get_site_files': get_site_files,
                         'delete_site': delete_site,
                         'delete_all_sites': delete_all_sites,
                         'deploy_folder': deploy_folder,
                         'list_sites': list_sites}
    # Create site parser
    create_site_parser = subparsers.add_parser('create_site')
    create_site_parser.add_argument('--name', type=str,
                                    help='Site name')
    create_site_parser.add_argument('--domain', type=str,
                                    help='Site domain')
    # Get site parser
    get_site_parser = subparsers.add_parser('get_site')
    get_site_parser.add_argument('site_id_or_domain', type=str)
    # Get site files parser
    get_site_files_parser = subparsers.add_parser('get_site_files')
    get_site_files_parser.add_argument('site_id', type=str)
    # Deploy folder parser
    deploy_folder_parser = subparsers.add_parser('deploy_folder')
    deploy_folder_parser.add_argument('--site-id', required=True,
                                      type=str)
    deploy_folder_parser.add_argument('folder', type=str)
    # List sites parser
    subparsers.add_parser('list_sites')
    # Delete site parser
    delete_site_parser = subparsers.add_parser('delete_site')
    delete_site_parser.add_argument('site_id', type=str)
    # Delete all sites parser
    subparsers.add_parser('delete_all_sites')
    # END PARSER DECLARATIONS
    # #######################
    args = argparser.parse_args()
    logging.basicConfig(level=getattr(logging, args.loglevel))
    mod_dir = os.path.dirname(__file__)
    cwd = os.getcwd()
    conf_filename = 'pynetlify.ini'
    configfile_paths = [
        os.path.join(cwd, conf_filename),
        os.path.join(mod_dir, conf_filename)]
    config = configparser.ConfigParser()
    for c_filepath in configfile_paths:
        if os.path.exists(c_filepath):
            config.read(c_filepath)
    auth_token = args.auth_token or config.get('netlify', 'auth-token')
    if not auth_token:
        logging.error('Could not find authentication token. '
                      'Config file lookup paths: %s',
                      ', '.join(configfile_paths))
    selected_action = available_actions.get(args.action)
    netlify_api = pynetlify.APIRequest(auth_token)
    selected_action(netlify_api, args)
    return 0
