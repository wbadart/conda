# This is just here so that tests is a package, so that dotted relative
# imports work.
from conda.gateways.logging import initialize_logging
import pytest
import sys
initialize_logging()

# Attempt to move any conda entries in PATH to the front of it.
# IDEs have their own ideas about how PATH should be managed and
# they do dumb stuff like add /usr/bin to the front of it
# meaning conda takes a submissve role and the wrong stuff
# runs (when other conda prefixes get activated they replace
# the wrongly placed entries with newer wrongly placed entries).
#
# Note, there's still condabin to worry about here, and also should
# we not remove all traces of conda instead of just this fixup?
# Ideally we'd have two modes, 'removed' and 'fixed'. I have seen
# condabin come from an entirely different installation than
# CONDA_PREFIX too in some instances and that really needs fixing.

import os
from os.path import dirname, normpath, join, isfile
from subprocess import check_output

def move_conda_to_front_of_PATH():
    if 'CONDA_PREFIX' in os.environ:
        from conda.activate import (PosixActivator, CmdExeActivator)
        if os.name == 'nt':
            activator_cls = CmdExeActivator
        else:
            activator_cls = PosixActivator
        activator = activator_cls()
        # But why not just use _replace_prefix_in_path? => because moving
        # the entries to the front of PATH is the goal here, not swapping
        # x for x (which would be pointless anyway).
        p = None
        # It might be nice to have a parameterised fixture with choices of:
        # 'System default PATH',
        # 'IDE default PATH',
        # 'Fully activated conda',
        # 'PATHly activated conda'
        # This will do for now => Note, if you have conda activated multiple
        # times it could mask some test failures but _remove_prefix_from_path
        # cannot be used multiple times; it will only remove *one* conda
        # prefix from the *original* value of PATH, calling it N times will
        # just return the same value every time, even if you update PATH.
        p = activator._remove_prefix_from_path(os.environ['CONDA_PREFIX'])
        new_path = os.pathsep.join(p)
        new_path = new_path.encode('utf-8') \
            if hasattr(new_path, 'encode') \
            else bytes(new_path, encoding='utf-8')
        os.environ['PATH'] = new_path
        activator = activator_cls()
        p = activator._add_prefix_to_path(os.environ['CONDA_PREFIX'])
        new_path = os.pathsep.join(p)
        new_path = new_path.encode('utf-8') \
            if hasattr(new_path, 'encode') \
            else bytes(new_path, encoding='utf-8')
        os.environ['PATH'] = new_path

def check_conda_versions_aligned():
    # Next problem. If we use conda to provide our git or otherwise do not
    # have it on PATH and if we also have no .version file then conda is
    # unable to figure out its version without throwing an exception. The
    # tests this broke most badly (test_activate.py) have a workaround of
    # installing git into one of the conda prefixes that gets used but it
    # is slow. Instead write .version if it does not exist, and also fix
    # it if it disagrees.

    version_file = normpath(join(dirname(dirname(__file__)), 'conda', '.version'))
    version_from_file = open(version_file, 'rt').read().split('\n')[0] if isfile(version_file) else None

    git_exe = 'git.exe' if sys.platform == 'win32' else 'git'
    version_from_git = None
    for pe in os.environ['PATH'].split(os.pathsep):
        if isfile(join(pe, git_exe)):
            try:
                version_from_git = check_output(join(pe, git_exe) + ' describe').decode('utf-8').split('\n')[0]
                break
            except:
                continue
    if not version_from_git:
        print("WARNING :: Could not check versions.")

    if version_from_git and version_from_git != version_from_file:
        print("WARNING :: conda/.version ({}) and git describe ({}) disagree, rewriting .version".format(
            version_from_git, version_from_file))
        with open(version_file, 'w') as fh:
            fh.write(version_from_git)


move_conda_to_front_of_PATH()
check_conda_versions_aligned()
