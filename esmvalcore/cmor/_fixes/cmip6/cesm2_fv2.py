"""Fixes for CESM2-FV2 model."""
from .cesm2 import Cl as BaseCl
from .cesm2 import Tas as BaseTas

from ..fix import Fix
import numpy as np
import iris

Cl = BaseCl


Cli = Cl


Clw = Cl


Tas = BaseTas


class AllVars(Fix):
    """Fixes for all vars."""
    def fix_metadata(self, cubes):
        """Fix daily timecoord and bounds.

        Issue
        -----
        Bounds might be wrong by one day
        DimCoord([2010-01-01 00:00:00, 2010-01-02 00:00:00, ...],
            bounds=[[2009-12-31 00:00:00, 2010-01-01 00:00:00],
                    [2010-01-01 00:00:00, 2010-01-02 00:00:00], ...], ...)
        For SSPs bounds of 2015-01-01 violate strictly monotonic rule:
            bounds=[[2015-01-01 00:00:00, 2015-01-01 00:00:00],..]
            leading to time coordinate treated as aux coord

        Parameters
        ----------
        cubes : iris.cube.CubeList
            Input cubes.

        Returns
        -------
        iris.cube.CubeList

        """
        cube = self.get_cube_from_list(cubes)
        if cube.attributes['mipTable'] == 'day':
            # coorect time coord points and bounds
            time = cube.coord('time')
            times = time.units.num2date(time.points)
            if np.all(np.array([c.hour for c in times]) == 0):
                time.points = time.points + 0.5
                time.bounds = None
                time.guess_bounds()
            # set time to dim_coord
            if time not in cube.coords(dim_coords=True):
                iris.util.promote_aux_coord_to_dim_coord(cube, 'time')
        return cubes
