from .exceptions import VectorError
from . import vector_defines as v_def
from .vector_can import vc_class
from . import vector_class as v_class

try:
    from . import vector_driver as v_driver
except Exception as exc:
    raise IOError("vector library is not loaded", exc)

from .vector_hw_api import VectorApi
from .vector_can.api import VectorCanApi
