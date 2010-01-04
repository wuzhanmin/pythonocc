#!/usr/bin/env python

##Copyright 2008-2009 Thomas Paviot (tpaviot@gmail.com)
##
##This file is part of pythonOCC.
##
##pythonOCC is free software: you can redistribute it and/or modify
##it under the terms of the GNU General Public License as published by
##the Free Software Foundation, either version 3 of the License, or
##(at your option) any later version.
##
##pythonOCC is distributed in the hope that it will be useful,
##but WITHOUT ANY WARRANTY; without even the implied warranty of
##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##GNU General Public License for more details.
##
##You should have received a copy of the GNU General Public License
##along with pythonOCC.  If not, see <http://www.gnu.org/licenses/>.

import glob
import os,os.path
import sys

import shutil
import time
# distutils stuff, necessary to customize compiler settings and setup the pythonOCC package
import distutils
from distutils.core import setup, Extension
from distutils import sysconfig
from distutils.command.build_ext import build_ext as _build_ext

sys.path.append(os.path.join(os.getcwd(),'wrapper'))
import Modules
#from environment import VERSION
import environment
# Try to import multiprocessing(python2.6 or higher) or processing(python2.5) packages
try:
    import multiprocessing as processing
    ncpus = processing.cpu_count()
    #print "Enabled multiprocess compilation for %i cpu(s)"%nprocs
    HAVE_MULTIPROCESSING = True
except:
    HAVE_MULTIPROCESSING = False

init_time = time.time()

if '--enable-geom' in sys.argv:
    WRAP_SALOME_GEOM = True #overload default behaviour
    sys.argv.remove('--enable-geom')
else:
    WRAP_SALOME_GEOM = False

# Check whether Salome GEOM package must be wrapped. True by default.
if '--enable-smesh' in sys.argv:
    WRAP_SALOME_SMESH = True #overload default behaviour
    sys.argv.remove('--enable-smesh')
else:
    WRAP_SALOME_SMESH = False

#Check whether build a 'all_in_one' distro (for Win32)
if '--all_in_one' in sys.argv and sys.platform=='win32':
    ALL_IN_ONE = True #overload default behaviour
    sys.argv.remove('-ALL_IN_ONE')
else:
    ALL_IN_ONE = False

#Windows hack to enable 'multiprocess compilation'
if '--reverse' in sys.argv and sys.platform=='win32':
    ALL_IN_ONE = True #overload default behaviour
    sys.argv.remove('--reverse')
    Modules.MODULES.reverse()
else:
    ALL_IN_ONE = False

#Add an option to tell setup.py to build only SMESH
if '--smesh-only' in sys.argv:
    SMESH_ONLY = True #overload default behaviour
    sys.argv.remove('--smesh-only')
else:
    SMESH_ONLY = False
    
#Check whether the -j nprocs option is passed
nprocs = 1 #by default, jut 1 proc
for elem in sys.argv:
    if elem[:2]=='-j':
        nprocs = int(elem.split('-j')[1])
        sys.argv.remove(elem)
        break

#Check whether the --with-boost-include option is passed
for elem in sys.argv:
    if elem.startswith('--with-boost-include='):
        environment.BOOST_INC = elem.split('--with-boost-include=')[1]
        sys.argv.remove(elem)
        break
    
#Check whether the --with-occ-include option is passed
for elem in sys.argv:
    if elem.startswith('--with-occ-include='):
        environment.OCC_INC = elem.split('--with-occ-include=')[1]
        sys.argv.remove(elem)
        break

#Check whether the --with-occ-lib option is passed
for elem in sys.argv:
    if elem.startswith('--with-occ-lib='):
        environment.OCC_LIB = elem.split('--with-occ-lib=')[1]
        sys.argv.remove(elem)
        break
    
#Check whether the --with-smesh-lib option is passed
for elem in sys.argv:
    if elem.startswith('--with-smesh-lib='):
        environment.SALOME_SMESH_LIB = elem.split('--with-smesh-lib=')[1]
        sys.argv.remove(elem)
        break
    
#Check whether the --with-geom-lib option is passed
for elem in sys.argv:
    if elem.startswith('--with-geom-lib='):
        environment.SALOME_GEOM_LIB = elem.split('--with-geom-lib=')[1]
        sys.argv.remove(elem)
        break

def check_occ_lib(library):
    ''' Find OCC shared library
    '''
    print 'Checking OCC %s library ...'%library,
    found = glob.glob(os.path.join(environment.OCC_LIB,'*%s*'%library))
    if len(found)>0:
        print 'yes'
        return True
    else:
        print 'no'
        return False

def check_salomegeom_lib(library):
    ''' Find salomegeometry shared library
    '''
    print 'Checking salomegeometry %s library ...'%library,
    found = glob.glob(os.path.join(environment.SALOME_GEOM_LIB,'*%s*'%library))
    if len(found)>0:
        print 'yes'
        return True
    else:
        print 'no'
        return False

def check_salomesmesh_lib(library):
    ''' Find salomesmesh shared library
    '''
    print 'Checking salomesmesh %s library ...'%library,
    found = glob.glob(os.path.join(environment.SALOME_SMESH_LIB,'*%s*'%library))
    if len(found)>0:
        print 'yes'
        return True
    else:
        print 'no'
        return False
    
def check_file(file,message):
    ''' Function used to find headers, lib etc. necessary for compilation
    '''
    print 'Checking %s ...'%message,
    if os.path.isfile(file):
        print 'yes'
        return True
    else:
        print 'no'
        return False

def check_config():
    ''' Checks all
    '''
    print "Building pythonOCC-%s for %s"%(environment.VERSION,sys.platform)
    # OCC includes and lib
    h = standard_transient_header = os.path.join(environment.OCC_INC,'Standard_Transient.hxx')
    if not check_file(standard_transient_header,'OCC Standard_Transient.hxx header'):
        print 'Error: the include path provided (%s) does not seem to contain all OCC headers. Please check that all OCC headers are located in this directory.'%environment.OCC_INC
        print 'pythonOCC compilation failed.'
        sys.exit(0) #exits, since compilation will fail
    l = check_occ_lib('TKernel')
    if not l:
        print 'libTKernel not found (part of OpenCASCADE). pythonOCC compilation aborted'
        sys.exit(0)
    # salomegeometry
    if WRAP_SALOME_GEOM:
        geom_object_header = os.path.join(environment.SALOME_GEOM_INC,'GEOMAlgo_Algo.hxx')
        h = check_file(geom_object_header,'salomegeometry GEOMAlgo_Algo.hxx header')
        if not h:
            print 'GEOMAlgo_Algo.hxx header file not found. pythonOCC compilation aborted'
            sys.exit(0)
        l = check_salomegeom_lib('Sketcher')
        if not l:
            print 'libSketcher not found (part of salomegeometry). pythonOCC compilation aborted'
            sys.exit(0)
    # salomesmesh
    if WRAP_SALOME_SMESH:
        smesh_mesh_header = os.path.join(environment.SALOME_SMESH_INC,'SMESH_Mesh.hxx')
        h = check_file(smesh_mesh_header,'salomesmesh SMESH_Mesh.hxx header')
        if not h:
            print 'SMESH_Mesh.hxx header file not found. pythonOCC compilation aborted'
            sys.exit(0)
        l = check_salomesmesh_lib('Driver')
        if not l:
            print 'libDriver not found (part of salomesmesh). pythonOCC compilation aborted'
            sys.exit(0)
        # BOOST
        shared_ptr_header = os.path.join(environment.BOOST_INC,'boost','shared_ptr.hpp')
        b = check_file(shared_ptr_header,'boost/shared_ptr.hpp header')
        if not b:
            print 'boost/shared_ptr.hpp header not found. pythonOCC compilation aborted'
            sys.exit(0)

check_config()

#Check whether the -j nprocs is passed
if ('-help' in sys.argv) or ('-h' in sys.argv):
    help_str="""pythonOCC setup - (c) Thomas Paviot, 2008-2009.
Usage: python setup.py build install[options]
With [options]:
    --enable-geom: tells setup.py to wrap Salome_GEOM library
    --enable-smesh: tells setup.py to wrap Salome_SMESH library
    -jNPROCS: number of processes to use
    --with-occ-include: location of opencascade includes
    --with-occ-lib: location of opencascade libs
    --with-salomegeom: location of salomegeom libs
    --with-smesh-lib: location of salomesmesh libs
    --with-boost-include: boost include directory location
    -ccompiler: compiler can be either 'gcc', 'mingw32' or 'msvc'
Examples:
    - under Windows: python setup.py build --enable_geom -j2 -cmsvc install
    - under Windows, without the GEOM module: python setup.py build -cmsvc install
    - under Linux: python setup.py build --enable_geom --enable_smesh -j2
    """
    print help_str
    sys.exit(0)


if nprocs>1 and HAVE_MULTIPROCESSING:
    if ncpus == 1:#just one CPU, no need for multiprocess:
        MULTI_PROCESS_COMPILATION = False
    else:
        #nprocs = int(options.nprocs)
        MULTI_PROCESS_COMPILATION = True
elif nprocs>1 and not HAVE_MULTIPROCESSING:
    raise NameError('The multiprocessing module connt be found. You can''t compile in multiprocess mode.')
else:
    MULTI_PROCESS_COMPILATION = False

import customize_build


def get_build_ext_instance():
    return build_ext_instance

class build_ext(_build_ext):
    """Specialized Python source builder."""
    # implement whatever needs to be different...
    def __init__(self,*kargs):
        _build_ext.__init__(self,*kargs)
        self._extensions = []
        customize_build.build_ext_instance = self

    def build_extension(self,ext):
        ''' This method take the extensions, append them to a list, and pass it to a multiprocessing.Pool
        '''
        global build_lib
        build_lib = self.build_lib #stores the build_lib path in order to copy data files
        if MULTI_PROCESS_COMPILATION:
            self._extensions.append(ext)
            # Create Pool
            if len(self._extensions) == NB_EXT:
                pool = processing.Pool(nprocs)
                pool.map(customize_build.build_extension,self._extensions)
        else:
            customize_build.build_extension(ext)

# Create paths for compilation process
if not (os.path.isdir(os.path.join(os.getcwd(),'OCC'))):
        os.mkdir(os.path.join(os.getcwd(),'OCC'))
if not (os.path.isdir(os.path.join(os.getcwd(),'build'))):
        os.mkdir(os.path.join(os.getcwd(),'build'))
if not (os.path.isdir(environment.SWIG_OUT_DIR)):
        os.mkdir(environment.SWIG_OUT_DIR)                 
#
# Package Name
#
PACKAGE = 'OCC'

def Create__init__():
    """
    Create the __init__.py file for OCC package.
    just create domething like: __all__ = ['gp,'gce']
    """
    print "Creating __init__.py script."
    init_directory = environment.SWIG_OUT_DIR#os.path.join(os.getcwd(),'OCC')
    if not os.path.isdir(init_directory):
        os.mkdir(init_directory)
    init_fp = open(os.path.join(init_directory,'__init__.py'),'w')
    #
    # if it is 'all_in_one' build, then the __init__.py script sets the env CSF_GraphicShr:
    #
    if ALL_IN_ONE and sys.platform=='win32':
        init_fp.write('import os\n')
        init_fp.write('import sys\n')
        init_fp.write("os.environ['CSF_GraphicShr'] = os.path.join(__path__[0],'TKOpenGl.dll')\n")
    #
    # Include Version number
    #
    init_fp.write("VERSION='%s'\n"%environment.VERSION)
    init_fp.write('__all__=[')
    for module_tuple in Modules.MODULES:
        module_name = module_tuple[0]
        init_fp.write("'%s',\n"%module_name)
    init_fp.write("'Visualization',\n'Misc'\n")
    init_fp.write(']\n')
    init_fp.close()
    print "__init__.py script created."

def install_file(full_filename):
    ''' Copy the file full_filename to the install dir. This Step is required because of the
    bad behaviour of distutils onlinux2 platforms
    '''
    install_dir = os.path.join(os.getcwd(),build_lib,'OCC')
    filename = os.path.basename(full_filename)
    shutil.copy(full_filename, os.path.join(install_dir,filename))
    print 'Copying %s->%s'%(full_filename,install_dir)
    
#
# OpenCascade libs
#
libraries = ['BinLPlugin', 'BinPlugin', 'BinXCAFPlugin', 'FWOSPlugin', 'mscmd', 'PTKernel',\
             'StdLPlugin', 'StdPlugin', 'TKAdvTools', 'TKBin', 'TKBinL', 'TKBinTObj', 'TKBinXCAF',\
             'TKBO', 'TKBool', 'TKBRep', 'TKCAF', 'TKCDF', 'TKCDLFront', 'TKCPPClient', 'TKCPPExt',\
             'TKCPPIntExt', 'TKCPPJini', 'TKCSFDBSchema', 'TKDCAF', 'TKDraw', 'TKernel',\
             'TKFeat', 'TKFillet', 'TKG2d', 'TKG3d', 'TKGeomAlgo', 'TKGeomBase', 'TKHLR', 'TKIDLFront',\
             'TKIGES', 'TKjcas','TKLCAF', 'TKMath', 'TKMesh', 'TKMeshVS', 'TKNIS', 'TKOffset',\
             'TKOpenGl', 'TKPCAF', 'TKPLCAF', 'TKPrim', 'TKPShape', 'TKService', 'TKShapeSchema',\
             'TKShHealing', 'TKStdLSchema', 'TKStdSchema', 'TKSTEP', 'TKSTEP209', 'TKSTEPAttr',\
             'TKSTEPBase', 'TKSTL', 'TKTCPPExt', 'TKTObj', 'TKTObjDRAW', 'TKTopAlgo', 'TKTopTest',\
             'TKV2d', 'TKV3d', 'TKViewerTest', 'TKVRML', 'TKWOK', 'TKWOKTcl', 'TKXCAF', 'TKXCAFSchema',\
             'TKXDEDRAW', 'TKXDEIGES', 'TKXDESTEP', 'TKXMesh', 'TKXml', 'TKXmlL', 'TKXmlTObj',\
             'TKXmlXCAF', 'TKXSBase', 'TKXSDRAW', 'XCAFPlugin',\
             'XmlLPlugin', 'XmlPlugin', 'XmlXCAFPlugin']
# Find the lib in OCC_LIB path and add it to the LIBS list
LIBS = []
for library in libraries:
    if check_occ_lib(library):
        LIBS.append(library)
#
# Salome Geom libs
#
GEOM_LIBS = ['Sketcher','ShHealOper','Partition','NMTTools',\
                        'NMTDS','GEOM','GEOMImpl',
                        'GEOMAlgo','Archimede']
if WRAP_SALOME_GEOM:
    for library in GEOM_LIBS:
        if not check_salomegeom_lib(library):
            print 'Error. pythonOCC compilation aborted'
            sys.exit(0)
#
# Salome SMESH libs
#
SMESH_LIBS = ['Driver','DriverDAT','DriverSTL','DriverUNV',\
                        'SMDS','SMESH',
                        'SMESHDS','StdMeshers'
                        ]
if WRAP_SALOME_SMESH:
    for library in SMESH_LIBS:
        if not check_salomesmesh_lib(library):
            print 'Error. pythonOCC compilation aborted'
            sys.exit(0)

if __name__=='__main__': #hack to enable multiprocessing under Windows
    extension = []
    if not SMESH_ONLY:
        for module in Modules.MODULES:
            SWIG_source_file = os.path.join(os.getcwd(),environment.SWIG_FILES_PATH_MODULAR,"%s.i"%module[0])
            if not (os.path.isfile(SWIG_source_file)):
                raise NameError('Missins swig file:%s'%SWIG_source_file)
            module_extension = Extension("OCC._%s"%module[0],
                            sources = [SWIG_source_file],
                            include_dirs=[environment.OCC_INC,environment.SWIG_FILES_PATH_MODULAR], #for TopOpeBRep_tools.hxx
                            library_dirs=[environment.OCC_LIB,environment.SALOME_GEOM_LIB,environment.SALOME_SMESH_LIB],
                            define_macros= environment.DEFINE_MACROS,
                            swig_opts = environment.SWIG_OPTS,
                            libraries = LIBS,
                            extra_compile_args = environment.ECA,
                            extra_link_args = environment.ELA,
                            )
            extension.append(module_extension)
        # Add Visualization
        extension.append(Extension("OCC._Visualization",
                            sources = [os.path.join(os.getcwd(),'wrapper','Visualization','Visualization.i'),
                                       os.path.join(os.getcwd(),'wrapper','Visualization','Display3d.cpp'),
                                       os.path.join(os.getcwd(),'wrapper','Visualization','Display2d.cpp'),
                                       os.path.join(os.getcwd(),'wrapper','Visualization','NISDisplay3d.cpp'),
                                       ],
                            include_dirs=[environment.OCC_INC,os.path.join(os.getcwd(),'wrapper','Visualization')],
                            library_dirs=[environment.OCC_LIB,environment.SALOME_GEOM_LIB,environment.SALOME_SMESH_LIB],
                            define_macros= environment.DEFINE_MACROS,
                            swig_opts = environment.SWIG_OPTS,
                            libraries = LIBS,
                            extra_compile_args = environment.ECA,
                            extra_link_args = environment.ELA,
                            ))
        # Add Misc
        extension.append(Extension("OCC._Misc",
                            sources = [os.path.join(os.getcwd(),'wrapper','Misc','Misc.i')],
                            include_dirs=[environment.OCC_INC],
                            library_dirs=[environment.OCC_LIB,environment.SALOME_GEOM_LIB,environment.SALOME_SMESH_LIB],
                            define_macros= environment.DEFINE_MACROS,
                            swig_opts = environment.SWIG_OPTS,
                            libraries = LIBS,
                            extra_compile_args = environment.ECA,
                            extra_link_args = environment.ELA,
                            ))
        #
        # Salome Geom extensions
        #
    if WRAP_SALOME_GEOM:
        for module in Modules.SALOME_GEOM_MODULES:
            SWIG_source_file = os.path.join(os.getcwd(),environment.SWIG_FILES_PATH_MODULAR,"%s.i"%module[0])
            if not (os.path.isfile(SWIG_source_file)):
                raise NameError('Missins swig file:%s'%SWIG_source_file)
            module_extension = Extension("OCC._%s"%module[0],
                        sources = [SWIG_source_file],
                        include_dirs=[environment.OCC_INC,environment.SALOME_GEOM_INC,environment.SWIG_FILES_PATH_MODULAR],
                        library_dirs=[environment.OCC_LIB,environment.SALOME_GEOM_LIB,environment.SALOME_SMESH_LIB],
                        define_macros= environment.DEFINE_MACROS,
                        swig_opts = environment.SWIG_OPTS,
                        libraries = LIBS + GEOM_LIBS,
                        extra_compile_args = environment.ECA,
                        extra_link_args = environment.ELA,
                        )
            extension.append(module_extension)
    
    #
    # Salome SMESH extensions
    #
    if WRAP_SALOME_SMESH:
        for module in Modules.SALOME_SMESH_MODULES:
            SWIG_source_file = os.path.join(os.getcwd(),environment.SWIG_FILES_PATH_MODULAR,"%s.i"%module[0])
            #if GENERATE_SWIG or not (os.path.isfile(SWIG_source_file)):
            if not (os.path.isfile(SWIG_source_file)):
                raise NameError('Missins swig file:%s'%SWIG_source_file)
            INCLUDE_DIRS = [environment.OCC_INC,environment.SALOME_SMESH_INC,environment.SWIG_FILES_PATH_MODULAR] #for TopOpeBRep_tools.hxx
            INCLUDE_DIRS.append(environment.BOOST_INC)
            module_extension = Extension("OCC._%s"%module[0],
                        sources = [SWIG_source_file],
                        include_dirs=INCLUDE_DIRS,
                        library_dirs=[environment.OCC_LIB,environment.SALOME_GEOM_LIB,environment.SALOME_SMESH_LIB],
                        define_macros= environment.DEFINE_MACROS,
                        swig_opts = environment.SWIG_OPTS,
                        libraries = LIBS + SMESH_LIBS,
                        extra_compile_args = environment.ECA,
                        extra_link_args = environment.ELA,
                        )
            extension.append(module_extension)
    
    NB_EXT = len(extension)
    
    KARGS = {"ext_modules":extension}
    #
    # SETUP
    #
    if ALL_IN_ONE and sys.platform=='win32':
        package_name = "pythonOCC-all_in_one"
    else:
        package_name = "pythonOCC"
    #
    # Create __init__ script
    #
    Create__init__()

    setup(cmdclass={'build_ext': build_ext},
          name = package_name,
          license = "GNU General Public License v3",
          url = "http://www.pythonocc.org",
          author = "Thomas Paviot, Jelle Feringa",
          author_email = "tpaviot@gmail.com, jelleferinga@gmail.com",
          description = "A CAD/PLM development library for the python programming language",
          version=environment.VERSION,
          long_description = """PythonOCC is a Python wrapper module for the
    OpenCascade library. It contains python functions and classes
    that will allow you to fully utilitize the OpenCascade library.
    This version is built against OpenCascade 6.3.0""",
          package_dir = {'OCC.Display':os.path.join(os.getcwd(),'addons','Display'),
                         'OCC.Utils':os.path.join(os.getcwd(),'addons','Utils'),
                         'OCC.Utils.DataExchange':os.path.join(os.getcwd(),'addons','Utils','DataExchange'),
                         'OCC.Toolkits':os.path.join(os.getcwd(),'wrapper','Toolkits'),
                         'OCC.Toolkits.FoundationClasses':os.path.join(os.getcwd(),'wrapper','Toolkits','FoundationClasses'),
                         'OCC.Toolkits.ModelingData':os.path.join(os.getcwd(),'wrapper','Toolkits','ModelingData'),
                         'OCC.PAF':os.path.join(os.getcwd(),'addons','PAF'),
                         'OCC.KBE':os.path.join(os.getcwd(),'addons','KBE')},
          packages = ['OCC.Display','OCC.Utils','OCC.Utils.DataExchange','OCC.PAF','OCC.Toolkits',\
                      'OCC.KBE',\
                      'OCC.Toolkits.FoundationClasses',\
                      'OCC.Toolkits.ModelingData'],
          #py_modules = ['OCC.Standard'],
          #data_files = data,
          **KARGS
          )
    #
    # Copy all the python modules to the root package dir
    # It's done only when 'build' or 'install' is in sys.argv
    if 'build' in sys.argv:
        modules_to_install = glob.glob(os.path.join(environment.SWIG_OUT_DIR,'*.py'))
        for module_to_install in modules_to_install:
            install_file(module_to_install)
        # install AUTHORS and LICENSE files
        authors_file = os.path.join(os.getcwd(),'..','AUTHORS')
        install_file(authors_file)
        license_file =  os.path.join(os.getcwd(),'..','LICENSE')
        install_file(license_file)
        # install GarbageCollector
        garbage_file = os.path.join(os.getcwd(),'wrapper','GarbageCollector.py')
        install_file(garbage_file)
        # install background image
        image_file = os.path.join(os.getcwd(),'addons','Display','default_background.bmp')
        bg_image_dest = os.path.join(os.getcwd(),build_lib,'OCC','Display','default_background.bmp')
        shutil.copy(image_file, bg_image_dest)
        
    final_time = time.time()
    print 'Compilation processed in %fs'%(final_time-init_time)
