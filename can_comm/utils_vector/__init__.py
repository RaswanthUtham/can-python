"""
    created on oct 2020

    :file: __init__.py
    :platform: Windows
    :synopsis:
        Implementation of vector hardware interface
        Refer vector can_comm driver documentation (XL Driver) for further details
        https://assets.vector.com/cms/content/products/XL_Driver_Library/Docs/XL_Driver_Library_Manual_EN.pdf
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""
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
