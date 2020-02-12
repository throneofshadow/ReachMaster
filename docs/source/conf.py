# -- Project information -----------------------------------------------------
# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

import os
import sys
import sphinx_rtd_theme

# -- Path setup --------------------------------------------------------------

# Set the software project root dirs
reach_master_root = os.path.join(os.path.dirname(os.path.dirname(os.getcwd())),"software/reach_master")
preprocessing_root = os.path.join(os.path.dirname(os.path.dirname(os.getcwd())),"software/preprocessing")

# Insert the project root dir as the first element in the PYTHONPATH.
# This lets us ensure that the source package is imported, and that its
# version is used.
sys.path.append(reach_master_root)
sys.path.append(preprocessing_root)

# -- Project information -----------------------------------------------------
project = 'ReachMaster'
copyright = 'The Regents of the University of California, through Lawrence Berkeley National Laboratory'
author = 'Brian Gereke'

# The full version, including alpha/beta/rc tags
version = '0.0.0'
release = 'alpha'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
	'sphinx.ext.autodoc',
	'sphinx.ext.napoleon',
	'sphinx_rtd_theme',
	'sphinx.ext.todo',
	'sphinx.ext.viewcode',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.githubpages',
    'sphinx.ext.mathjax',
    'sphinx.ext.autosectionlabel'
]

#Options for Napolean extension
napoleon_google_docstring = False
napoleon_numpy_docstring = True

#Options for todo extension
todo_include_todos = True

#tell autodoc which imports to mock
autodoc_mock_imports = [
    'serial',
    'ximea',
    'cv2'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_logo = 'art/splinter.png'
html_theme_options = {'logo_only': False}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']
html_static_path = []

