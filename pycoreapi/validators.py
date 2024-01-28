from pycoreapi.utils import is_extra_installed

if is_extra_installed('pydantic'):
    from typing import Type, TypeVar, Optional, Any
    from pydantic import BaseModel


    class Validator(BaseModel):
        headers: Optional[Any]
        query: Optional[Any]
        body: Optional[Any]
else:
    raise ImportError("The 'coreapi[pydantic]' extra is required to import Validator from validators.py. "
                      "Please install it using: pip install coreapi[pydantic]")