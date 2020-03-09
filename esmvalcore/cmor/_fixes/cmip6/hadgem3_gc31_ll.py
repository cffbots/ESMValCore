"""Fixes for CMIP6 HadGEM-GC31-LL."""
from .ukesm1_0_ll import AllVars as BaseAllVars
from .ukesm1_0_ll import Cl as BaseCl


class AllVars(BaseAllVars):
    """Fixes for all vars."""


class Cl(BaseCl):
    """Fixes for ``cl``."""


class Clw(Cl):
    """Fixes for ``clw``."""


class Cli(Cl):
    """Fixes for ``cli``."""
