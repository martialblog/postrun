#!/usr/bin/env python3


import pytest
import os
import tempfile
import subprocess
import unittest.mock as mock

import postrun


@pytest.fixture(scope='session')
def temp_dir(tmpdir_factory):

    temp_dir = tmpdir_factory.mktemp('etc')
    return temp_dir


@pytest.fixture(scope='session')
def etc_puppetlabs(temp_dir):

    puppetlabs_dir = os.path.join(str(temp_dir), 'puppetlabs', 'code', 'environments')
    os.makedirs(puppetlabs_dir)

    return puppetlabs_dir


@pytest.fixture
def module():

    mod = {'roles': {'ref': 'production', 'url': 'https://github.com/vision-it/puppet-roles.git'}}
    return mod


@pytest.mark.util
@mock.patch('shutil.rmtree')
@mock.patch('os.makedirs')
def test_clear_folder(mock_mkdir, mock_rm):

    postrun.clear_folder('/puppet/foobar')
    mock_rm.assert_called_once_with('/puppet/foobar')
    mock_mkdir.assert_called_once_with('/puppet/foobar')


@pytest.mark.util
def test_load_yaml(module):

    directory = os.path.dirname(os.path.realpath(__file__))
    testfile = os.path.join(directory, "modules.yaml")
    loaded_mod = postrun.load_yaml(testfile)

    assert(module == loaded_mod['modules']['default'])


@pytest.mark.git
@mock.patch('subprocess.check_call')
def test_clone_module(mock_call):

    module = ('roles', {'url': 'https://github.com/vision-it/puppet-roles.git', 'ref': 'production'})

    process_mock = mock.Mock()
    attrs = {'return_value': (b'output', b'error')}
    process_mock.configure_mock(**attrs)
    mock_call.return_value = process_mock

    postrun.clone_module(module, '/foobar')

    mock_call.assert_called_once_with(['git',
                                       'clone',
                                       'https://github.com/vision-it/puppet-roles.git',
                                       '-b',
                                       'production',
                                       '/foobar/roles'],
                                      stderr=-1,
                                      stdout=-1)


@pytest.mark.util
def test_is_vagrant():

    virtual = postrun.is_vagrant()
    assert(virtual == False)


@pytest.mark.util
@mock.patch('subprocess.Popen')
def test_get_location(mock_popen):

    process_mock = mock.Mock()
    attrs = {'communicate.return_value': (b'output', b'error')}
    process_mock.configure_mock(**attrs)
    mock_popen.return_value = process_mock

    location = postrun.get_location()

    mock_popen.assert_called_once_with('facter location',
                                       close_fds=True,
                                       shell=True,
                                       stderr=-2,
                                       stdin=-1,
                                       stdout=-1)

    assert(location == 'output')


@pytest.mark.modules
def test_load_modules_real_env(module):

    expected_mod = {'other_mod': {'ref': 'master', 'url': 'https://github.com/vision-it/puppet-roles.git'}}

    directory = os.path.dirname(os.path.realpath(__file__))
    loaded_mod = postrun.load_modules(directory, location='real_loc')

    assert(loaded_mod == expected_mod)


@pytest.mark.modules
def test_load_modules_no_loc(module):

    directory = os.path.dirname(os.path.realpath(__file__))
    loaded_mod = postrun.load_modules(directory, location='not_loc')

    assert(loaded_mod == module)


@pytest.mark.modules
def test_load_modules_no_file():

    mod = postrun.load_modules('/foobar', 'staging')
    assert(mod == {})


@pytest.mark.modules
@mock.patch('subprocess.check_call')
def test_deploy_modules(mock_call, etc_puppetlabs):

    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory, location='some_loc')

    postrun.deploy_modules(etc_puppetlabs, modules)

    # Gets called with 2 modules
    # The rest should be tested in clone_module
    assert(mock_call.call_count == 2)


@pytest.mark.util
def test_has_opt_module_false():

    return_val = postrun.has_opt_module('foobar')
    assert(return_val == False)

@pytest.mark.util
def test_has_opt_module_true(etc_puppetlabs):

    mod_dir = os.path.join(etc_puppetlabs, 'foobar')
    os.makedirs(mod_dir)

    return_val = postrun.has_opt_module(etc_puppetlabs, 'foobar')
    assert(return_val == True)


@pytest.mark.util
@mock.patch('shutil.rmtree')
@mock.patch('os.symlink')
def test_deploy_hiera(os_sym, mock_rm):

    postrun.deploy_hiera(hiera_dir='/hiera/foobar')

    mock_rm.assert_called_once_with('/hiera/foobar')
    os_sym.assert_called_once_with('/opt/puppet/hiera', '/hiera/foobar')


@pytest.mark.new
@mock.patch('postrun.deploy_hiera')
@mock.patch('postrun.clone_module')
@mock.patch('os.symlink')
def test_deploy_modules_vagrant_clone(mock_sym, mock_clone, mock_hiera):

    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory, location='some_loc')

    postrun.deploy_modules_vagrant('/foobar', modules)

    mock_hiera.assert_called_once_with('/etc/puppetlabs/code/hieradata/production')
    assert(mock_clone.call_count == 2)
    assert(mock_sym.call_count == 0)


@pytest.mark.new
@mock.patch('postrun.has_opt_module')
@mock.patch('postrun.deploy_hiera')
@mock.patch('postrun.clone_module')
@mock.patch('os.symlink')
def test_deploy_modules_vagrant_sym(mock_sym, mock_clone, mock_hiera, mock_hasmod):

    directory = os.path.dirname(os.path.realpath(__file__))
    modules = postrun.load_modules(directory, location='some_loc')
    mock_hasmod.return_value = True

    postrun.deploy_modules_vagrant('/foobar', modules)

    mock_hiera.assert_called_once_with('/etc/puppetlabs/code/hieradata/production')
    assert(mock_clone.call_count == 0)
    assert(mock_hasmod.call_count == 2)
    assert(mock_sym.call_count == 2)


@pytest.mark.todo
def test_main():
    pass
