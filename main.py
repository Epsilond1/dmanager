# coding: utf-8

"""
FIXME
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import docker
import os
import sys
from subprocess import Popen
from yaml import load, YAMLError

CONFIG_NAME = 'config.yaml'

class Instance(object):
    def __init__(self, service_name):
        self._service_name = service_name
        self._repo = ''
        self._workdir = ''
        self._image_name = ''
        self._secrets = ''
        self._client = docker.from_env()

    @staticmethod
    def run_command(*args, **kwargs):
        print('start ancestor-process with arguments: {}\n{}'.format(args, kwargs))
        exit_code = Popen(*args, **kwargs).wait()
        print('ancestor-process finished with code {}'.format(exit_code))
        assert exit_code == 0

    def load_config(self):
        must_params = {
            'repo': None,
            'workdir': None,
            'image_name': None,
            'secrets': None,
            'branch': None,
            'port_external': None,
            'port_internal': None,
            'protocol': None,
        }

        with open(CONFIG_NAME) as stream:
            try:
                try:
                    must_params.update(load(stream)[self._service_name])
                except KeyError:
                    print('not found application ', self._service_name)
                    return
            except YAMLError as exc:
                print('file reading error. text exceptions: ', exc)
                return

        broken_params = {k_: 'not found' for k_, v_ in must_params.items() if not v_}

        if broken_params:
            print('config\'s format is broken')
            print(broken_params)
            return

        self._repo = must_params['repo']
        self._workdir = must_params['workdir']
        self._image_name = must_params['image_name']
        self._secrets = must_params['secrets']
        self._branch = must_params['branch']

        self._port_external = must_params['port_external']
        self._port_internal = must_params['port_internal']
        self._protocol = must_params['protocol']

    def pull_revision(self):
        if not os.path.exists(self._workdir):
            self.run_command(['git', 'clone', self._repo, '.'])
        os.chdir(self._workdir)
        self.run_command(['git', 'checkout', self._branch])
        self.run_command(['git', 'fetch', '.'])
        print('git now is actually')

    def deploy(self):
        print('search started containers...')

        containers = self._client.containers.list(filters={'status': 'running', 'ancestor': self._image_name + ':latest'})
        if len(containers) > 1:
            print('found {} containers... This is problem'.format(len(containers)))
            return
        elif len(containers) == 1:
            print('container {} shutting down'.format(containers[0].image.tags))
            containers[0].stop()

        print('start build image')
        self._client.images.build(path=self._workdir, tag=self._image_name, dockerfile=self._workdir+'/Dockerfile', pull=True)
        print('building success finished')

        print('start build and run container')
        self._client.containers.run(self._image_name, ports={
            '{}/{}'.format(self._port_internal, self._protocol): int(self._port_external)
        }, detach=True)
        print('deploy success')

    def start_worker(self):
        self.pull_revision()
        self.deploy()

    def print_config(self):
        print(self._service_name)
        print(self._workdir)
        print(self._image_name)
        print(self._secrets)
        print(self._repo)


def __main__():
    if len(sys.argv) < 2:
        print('argument cli needed contains application name')
        return

    app_name = sys.argv[1]
    instance = Instance(app_name)
    instance.load_config()
    instance.start_worker()

__main__()
