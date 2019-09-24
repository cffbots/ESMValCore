# pylint: disable=invalid-name, no-self-use, too-few-public-methods
"""Fixes for UKESM1-0-LL."""
# import numpy as np
# import iris

from ..fix import Fix


class allvars(Fix):
    """Fixes for all vars."""

    def fix_metadata(self, cubelist):
        """
        Fix non-standard dimension names.

        Parameters
        ----------
        cubelist: iris CubeList
            List of cubes to fix

        Returns
        -------
        iris.cube.CubeList
        """
        assert 0
        for cube in cubelist:
            lats = cube.coord('latitude')
            lons = cube.coord('longitude')
            lats.var_name = 'lat'
            lons.var_name = 'lon'

            time = cube.coord('latitude')
            if time.units == 'days since 1850-01-01-00-00-00':
                time.units = 'days since 1850-01-01:00-00-00'

        return cubelist
