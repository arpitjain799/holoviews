"""
HoloViews makes data analysis and visualization simple
======================================================

HoloViews lets you focus on what you are trying to explore and convey, not on
the process of plotting.

HoloViews

- supports a wide range of data sources including Pandas, Dask, XArray
Rapids cuDF, Streamz, Intake, Geopandas, NetworkX and Ibis.
- supports the plotting backends Bokeh (default), Matplotlib and Plotly.
- allows you to drop into the rest of the
HoloViz ecosystem when more power or flexibility is needed.

For basic data exploration we recommend using the higher level hvPlot package,
which provides the familiar Pandas `.plot` api. You can drop into HoloViews
when needed.

To learn more check out https://holoviews.org/. To report issues or contribute
go to https://github.com/holoviz/holoviews. To join the community go to
https://discourse.holoviz.org/.

How to use HoloViews in 3 simple steps
--------------------------------------

Work with the data source you already know and ❤️

>>> import pandas as pd
>>> station_info = pd.read_csv('https://raw.githubusercontent.com/holoviz/holoviews/main/examples/assets/station_info.csv')

Import HoloViews and configure your plotting backend

>>> import holoviews as hv
>>> hv.extension('bokeh')

Annotate your data

>>> scatter = (
...     hv.Scatter(station_info, kdims='services', vdims='ridership')
...     .redim(
...         services=hv.Dimension("services", label='Services'),
...         ridership=hv.Dimension("ridership", label='Ridership'),
...     )
...     .opts(size=10, color="red", responsive=True)
... )
>>> scatter

In a notebook this will display a nice scatter plot.

Note that the `kdims` (The key dimension(s)) represents the independent
variable(s) and the `vdims` (value dimension(s)) the dependent variable(s).

For more check out https://holoviews.org/getting_started/Introduction.html

How to get help
---------------

You can understand the structure of your objects by printing them.

>>> print(scatter)
:Scatter   [services]   (ridership)

You can get extensive documentation using `hv.help`.

>>> hv.help(scatter)

In a notebook or ipython environment the usual

- `help` and `?` will provide you with documentation.
- `TAB` and `SHIFT+TAB` completion will help you navigate.

To ask the community go to https://discourse.holoviz.org/.
To report issues go to https://github.com/holoviz/holoviews.
"""
import os
import sys

import param

__version__ = str(param.version.Version(fpath=__file__, archive_commit="$Format:%h$",
                                        reponame="holoviews"))

from . import util                                       # noqa (API import)
from .annotators import annotate                         # noqa (API import)
from .core import archive, config                        # noqa (API import)
from .core.boundingregion import BoundingBox             # noqa (API import)
from .core.dimension import OrderedDict, Dimension       # noqa (API import)
from .core.element import Element, Collator              # noqa (API import)
from .core.layout import (Layout, NdLayout, Empty,       # noqa (API import)
                          AdjointLayout)
from .core.ndmapping import NdMapping                    # noqa (API import)
from .core.options import (Options, Store, Cycle,        # noqa (API import)
                           Palette, StoreOptions)
from .core.overlay import Overlay, NdOverlay             # noqa (API import)
from .core.spaces import (HoloMap, Callable, DynamicMap, # noqa (API import)
                          GridSpace, GridMatrix)

from .operation import Operation                         # noqa (API import)
from .element import *
from .element import __all__ as elements_list
from .selection import link_selections                   # noqa (API import)
from .util import (extension, renderer, output, opts,    # noqa (API import)
                   render, save)
from .util.transform import dim                          # noqa (API import)
from .util.warnings import HoloviewsDeprecationWarning, HoloviewsUserWarning  # noqa: F401

# Suppress warnings generated by NumPy in matplotlib
# Expected to be fixed in next matplotlib release
import warnings
warnings.filterwarnings("ignore",
                        message="elementwise comparison failed; returning scalar instead")

try:
    import IPython                 # noqa (API import)
    from .ipython import notebook_extension
    extension = notebook_extension # noqa (name remapping)
except ImportError:
    class notebook_extension(param.ParameterizedFunction):
        def __call__(self, *args, **opts): # noqa (dummy signature)
            raise Exception("IPython notebook not available: use hv.extension instead.")

if '_pyodide' in sys.modules:
    from .pyodide import pyodide_extension, in_jupyterlite
    # The notebook_extension is needed inside jupyterlite,
    # so the override is only done if we are not inside jupyterlite.
    if in_jupyterlite():
        extension.inline = False
    else:
        extension = pyodide_extension
    del pyodide_extension, in_jupyterlite

# A single holoviews.rc file may be executed if found.
for rcfile in [os.environ.get("HOLOVIEWSRC", ''),
               os.path.abspath(os.path.join(os.path.split(__file__)[0],
                                            '..', 'holoviews.rc')),
               "~/.holoviews.rc",
               "~/.config/holoviews/holoviews.rc"]:
    filename = os.path.expanduser(rcfile)
    if os.path.isfile(filename):
        with open(filename, encoding='utf8') as f:
            code = compile(f.read(), filename, 'exec')
            try:
                exec(code)
            except Exception as e:
                print(f"Warning: Could not load {filename!r} [{str(e)!r}]")
        del f, code
        break
    del filename

def help(obj, visualization=True, ansi=True, backend=None,
         recursive=False, pattern=None):
    """
    Extended version of the built-in help that supports parameterized
    functions and objects. A pattern (regular expression) may be used to
    filter the output and if recursive is set to True, documentation for
    the supplied object is shown. Note that the recursive option will
    only work with an object instance and not a class.

    If ansi is set to False, all ANSI color
    codes are stripped out.
    """
    backend = backend if backend else Store.current_backend
    info = Store.info(obj, ansi=ansi, backend=backend, visualization=visualization,
                      recursive=recursive, pattern=pattern, elements=elements_list)

    msg = ("\nTo view the visualization options applicable to this "
           "object or class, use:\n\n"
           "   holoviews.help(obj, visualization=True)\n\n")
    if info:
        print((msg if visualization is False else '') + info)
    else:
        import pydoc
        pydoc.help(obj)


del os, rcfile, warnings
