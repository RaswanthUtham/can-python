"""Types for mypy type-checking
"""

import typing

if typing.TYPE_CHECKING:
    import os

try:
    import mypy_extensions


    class TypeCheck:
        CanFilter = mypy_extensions.TypedDict("CanFilter", {"can_id": int, "can_mask": int})
        CanFilterExtended = mypy_extensions.TypedDict(
            "CanFilterExtended", {"can_id": int, "can_mask": int, "extended": bool}
        )

        CanFilters = typing.Sequence[typing.Union[CanFilter, CanFilterExtended]]

        CanData = typing.Union[bytes, bytearray, int, typing.Iterable[int]]

        # Used for the Abstract Base Class
        ChannelStr = str
        ChannelInt = int
        Channel = typing.Union[ChannelInt, ChannelStr]

        # vector bus
        v_channel = typing.Union[int, str, typing.List[int,]]

        AutoDetectedConfig = mypy_extensions.TypedDict(
            "AutoDetectedConfig", {"interface": str, "channel": Channel}
        )

        # Used by the IO module
        FileLike = typing.IO[typing.Any]
        StringPathLike = typing.Union[str, "os.PathLike[str]"]
        AcceptedIOType = typing.Optional[typing.Union[FileLike, StringPathLike]]

        BusConfig = typing.NewType("BusConfig", dict)


except ImportError:
    class TypeCheck:

        CanFilters = typing.Sequence[typing.Union[typing.Dict]]

        CanData = typing.Union[bytes, bytearray, int, typing.Iterable[int]]

        # Used for the Abstract Base Class
        ChannelStr = str
        ChannelInt = int
        Channel = typing.Union[ChannelInt, ChannelStr]

        # vector bus
        v_channel = typing.Union[int, str, typing.List[int,]]

        AutoDetectedConfig = typing.Dict[int, str]

        # Used by the IO module
        FileLike = typing.IO[typing.Any]
        StringPathLike = typing.Union[str, "os.PathLike[str]"]
        AcceptedIOType = typing.Optional[typing.Union[FileLike, StringPathLike]]

        BusConfig = typing.NewType("BusConfig", dict)
