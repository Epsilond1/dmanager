# coding: utf-8

"""
FIXME
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import git
import sys
from subprocess import Popen, PIPE, call
from yaml import load, YAMLError


class Instance(object):
    def __init__(self, service_name):
        self._service_name = service_name
        self.repo = ''
        self.workdir = ''
        self.image_name = ''
        self.secrets = ''

    def load_config(self):
        document = {
            'repo': None,
            'workdir': None,
            'image_name': None,
            'secrets': None
        }

        with open('config.yaml') as stream:
            try:
                try:
                    document.update(load(stream)[self._service_name])
                except KeyError:
                    print('not found application ', self._service_name)
                    raise KeyError
            except YAMLError as exc:
                print('file reading error. text exceptions: ', exc)
                raise

        broken_params = {k_: 'not found' for k_, v_ in document.items() if not v_}

        if broken_params:
            print('config\'s format is broken')
            print(broken_params)
            raise AttributeError

        self.repo = document['repo']
        self.workdir = document['workdir']
        self.image_name = document['image_name']
        self.secrets = document['secrets']

    def pull_revision(self):
        print('try pull')
        g = git.cmd.Git(self.workdir)
        g.pull()
        print('success')

    def deploy(self):
        container_id = ''
        with Popen(['docker', 'ps'], stdout=PIPE) as proc:
            out = proc.stdout.readlines()
            print(out)
            for line in out:
                if self.image_name.encode() in line.split():
                    container_id = line.split()[0].decode('utf-8')
                    break

        if container_id:
            exit_code = call(['docker', 'container', 'stop', container_id])
            if exit_code != 0:
                print('Vsyo ploxo')
                raise SystemError

        Popen(['docker', 'build', '-t', self.image_name, '.'], cwd=self.workdir)

        exit_code = call(['docker', 'run', '-d', '-p', '4000:80', self.image_name])
        if exit_code != 0:
            print('Container does not start')
            raise SystemError

        print('Deploy success')

    def start_worker(self):
        self.pull_revision()
        self.deploy()

    def print_config(self):
        print(self._service_name)
        print(self.workdir)
        print(self.image_name)
        print(self.secrets)
        print(self.repo)


def __main__():
    if len(sys.argv) < 2:
        print('argument cli needed contains application name')
        raise TypeError

    app_name = sys.argv[1]
    instance = Instance(app_name)
    instance.load_config()
    instance.start_worker()

__main__()
