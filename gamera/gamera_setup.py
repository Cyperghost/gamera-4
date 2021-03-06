# -*- mode: python; indent-tabs-mode: nil; tab-width: 3 -*-
# vim: set tabstop=3 shiftwidth=3 expandtab:
#
# Copyright (C) 2001-2005 Ichiro Fujinaga, Michael Droettboom,
#                          and Karl MacMillan
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""Utilities to make writing setup.py files for Gamera extensions easier"""

import sys
import os
import platform
import glob
from distutils.sysconfig import get_python_lib, get_python_inc, PREFIX
from distutils.command import install_data

# Fix RPM building
#
# This is a total hack to patch up an error in distutils.command.bdist_rpm
import distutils.command.bdist_rpm
def rpm_run(self):
   try:
      original_rpm_run(self)
   except AssertionError as e:
      if str(e).startswith("unexpected number of RPM files found"):
         rpms = glob.glob(os.path.join(os.path.join(self.rpm_base, 'RPMS'),
                                       "*/*.rpm"))
         for rpm in rpms:
            self.move_file(rpm, self.dist_dir)
      else:
         raise e
original_rpm_run = distutils.command.bdist_rpm.bdist_rpm.run
setattr(distutils.command.bdist_rpm.bdist_rpm, 'run', rpm_run)

class smart_install_data(install_data.install_data):
   def run(self):
      install_cmd = self.get_finalized_command("install")
      install_dir = os.path.join(getattr(install_cmd, "install_lib"), "gamera")
      print("INSTALL DIRECTORY", install_dir)
      output = []
      for path, files in self.data_files:
         if "$LIB" in path:
            path = path[path.find("$LIB"):]
            path = path.replace("$LIB", install_dir)
         output.append((path, files))
      self.data_files = output
      return install_data.install_data.run(self)


extras = {
   'extra_compile_args': [
      '-Wall',
      '-O2',
      '-std=c++11',
      '-Wunused-variable',
      '-Wwrite-strings',
      '-Wdeprecated-declarations',
      '-Wunknown-pragmas',
      '-Wformat'
   ]
}

cmdclass = {'install_data': smart_install_data}
if sys.platform == "darwin":
   from gamera.mac import gamera_mac_setup
   cmdclass['bdist_osx'] = gamera_mac_setup.bdist_osx
   extras['extra_compile_args'].append('-Wmacro-redefined')
elif sys.platform == "win32":
   try:
      from win32 import bdist_msi
      cmdclass['bdist_msi'] = bdist_msi.bdist_msi
   except ImportError:
      pass

# If gamera.generate is imported gamera.__init__.py will
# also be imported, which won't work until the build is
# finished. To get around this, the gamera directory is
# added to the path and generate is imported directly
sys.path.append("gamera")
from . import generate

if sys.platform == 'win32' and not '--compiler=mingw32' in sys.argv:
   extras['extra_compile_args'] = ['/GR','/EHsc']#, "/Zi"]
elif '--compiler=mingw32' in sys.argv or not sys.platform == 'win32':
   extras['libraries'] = ['stdc++'] # Not for intel compiler

# Check that we are running a recent enough version of Python.
# This depends on the platform.
default_required_version = 350
required_versions = {'linux2': 350, 'win32':  350, 'darwin': 350, 'cygwin': 350}
version = float(''.join([str(x) for x in sys.version_info[0:3]]))
required_version = required_versions.setdefault(sys.platform, default_required_version)
if version < required_version:
   print("Gamera requires Python version %s or later." % '.'.join(list(str(required_version))))
   print("You are running the following Python version:")
   print(sys.version)
   sys.exit(1)

lib_path = os.path.join(get_python_lib()[len(PREFIX)+1:], "gamera")
include_path = os.path.join(get_python_inc()[len(PREFIX)+1:], "gamera")

def get_plugin_filenames(path):
   """Return all of the python plugin files in a specified path. This is not
   the same as glob.glob('*.py') in that it removes __init__.py files and
   normalizes the path in an os independent way."""
   plugins = glob.glob(path + "/*.py")
   norm_plugins = []
   for x in plugins:
      norm_plugins.append(os.path.normpath(os.path.abspath(x)))
   plugins = norm_plugins
   try:
      path = os.path.normpath(os.path.abspath(path + "/__init__.py"))
      plugins.remove(path)
   except Exception:
      pass
   return plugins

def generate_plugins(plugins, location, compiling_gamera=0):
   """Generate the necessary cpp wrappers from a list of python plugin
   filenames. The regeneration only happens if it is necessary (either
   the python file has changed or one of the files that it depends on
   has changed). A distutiles extension class is created for each plugin
   that needs to be compiled."""

   # Create the list of modules to ignore at import - because
   # we are in the middle of the build process a lot of C++
   # plugins don't yet exist. By preventing the import of
   # the core of gamera and all of the plugins we allow the
   # plugins to be imported for the build process to examine
   # them. Some of this is unnecessary for external plugins,
   # but it shouldn't hurt.
   ignore = ["core", "gamera.core", "gameracore"]
   for x in plugins:
      plug_path, filename = os.path.split(x)
      module_name = "_" + filename.split('.')[0]
      ignore.append(module_name)
   generate.magic_import_setup(ignore)
   
   plugin_extensions = []
   for x in plugins:
      extension = generate.generate_plugin(
         x, location, compiling_gamera, **extras)
      if not extension is None:
         plugin_extensions.append(extension)
   
   generate.restore_import()
   return plugin_extensions

def get_gamera_include_dirs():
   # the "usr/local" prefix is for recent Ubunut versions, which
   # install addon modules no longer along with the python core
   return [os.path.join(get_python_inc(), "gamera"),
           os.path.join(get_python_inc(prefix="/usr/local"), "gamera"),
           os.path.join(get_python_inc(), "../gamera"),
           "/usr/include/gamera"]
