# coding: utf-8

"""
FIXME
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import docker
import git
import sys
from yaml import load, YAMLError


class Instance(object):
    def __init__(self, service_name):
        self._service_name = service_name
        self.repo = ''
        self.workdir = ''
        self.image_name = ''
        self.secrets = ''
        self.command = ''
        self.client = docker.from_env()

    def load_config(self):
        document = {
            'repo': None,
            'workdir': None,
            'image_name': None,
            'secrets': None,
            'command': None,
        }

        with open('config.yaml') as stream:
            try:
                try:
                    document.update(load(stream)[self._service_name])
                except KeyError:
                    print('not found application ', self._service_name)
                    return
            except YAMLError as exc:
                print('file reading error. text exceptions: ', exc)
                return

        broken_params = {k_: 'not found' for k_, v_ in document.items() if not v_}

        if broken_params:
            print('config\'s format is broken')
            print(broken_params)
            return

        self.repo = document['repo']
        self.workdir = document['workdir']
        self.image_name = document['image_name']
        self.secrets = document['secrets']
        self.command = document['command']

    def pull_revision(self):
        print('try pull')
        g = git.cmd.Git(self.workdir)
        g.pull()
        print('success')

    def deploy(self):
        print('search started containers...')

        containers = self.client.containers.list(filters={'status': 'running', 'ancestor': self.image_name + ':latest'})
        if len(containers) > 1:
            print('found {} containers... This is problem'.format(len(containers)))
            return
        elif len(containers) == 1:
            print('container {} shutting down'.format(containers[0].image.tags))
            containers[0].stop()

        print('start build image')
        self.client.images.build(path=self.workdir, tag=self.image_name, dockerfile=self.workdir+'/Dockerfile', pull=True)
        print('building success finished')

        print('start build and run container')
        self.client.containers.run(self.image_name, ports={'80/tcp': 4000}, detach=True)
        print('deploy success')

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
        return

    app_name = sys.argv[1]
    instance = Instance(app_name)
    instance.load_config()
    instance.start_worker()

__main__()
