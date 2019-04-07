"""Tests for the module :mod:`esmvaltool.diag_scripts.shared.io`."""
import os
from collections import OrderedDict
from copy import deepcopy

import iris
import mock
import numpy as np
import pytest
import yaml

from esmvaltool.diag_scripts.shared import io

with open(os.path.join(os.path.dirname(__file__), 'configs',
                       'test_io.yml')) as file_:
    CONFIG = yaml.safe_load(file_)


@pytest.mark.parametrize('data', CONFIG['_has_necessary_attributes'])
@mock.patch.object(io, 'logger', autospec=True)
def test_has_necessary_attributes(mock_logger, data):
    """Test attribute checks."""
    for log_level in ('debug', 'info', 'warning', 'error', 'exception'):
        metadata = data['input']
        kwargs = data.get('kwargs', {})
        has_atts = io._has_necessary_attributes(
            metadata, log_level=log_level, **kwargs)
        assert has_atts == data['output']
        logger_func = getattr(mock_logger, log_level)
        if has_atts:
            logger_func.assert_not_called()
        else:
            logger_func.assert_called()
        mock_logger.reset_mock()


CFG = {
    'input_files': [
        'metadata.yml',
        'test_metadata.yml',
        'valid/dir/1',
        'valid/dir/2',
    ],
    'other_attr':
    'I am not used!',
}
ROOT_DIR = '/root/to/something'
PATTERNS_FOR_ALL_ANCESTORS = [
    (None, [
        os.path.join(ROOT_DIR, 'test.nc'),
        os.path.join(ROOT_DIR, 'egg.yml'),
        os.path.join(ROOT_DIR, 'root2', 'x.nc'),
        os.path.join(ROOT_DIR, 'root2', 'y.png'),
        os.path.join(ROOT_DIR, 'root3', 'egg.nc'),
        os.path.join(ROOT_DIR, 'test_1.nc'),
        os.path.join(ROOT_DIR, 'test_2.yml'),
        os.path.join(ROOT_DIR, 'root4', 'egg.nc'),
    ]),
    ('*', [
        os.path.join(ROOT_DIR, 'test.nc'),
        os.path.join(ROOT_DIR, 'egg.yml'),
        os.path.join(ROOT_DIR, 'root2', 'x.nc'),
        os.path.join(ROOT_DIR, 'root2', 'y.png'),
        os.path.join(ROOT_DIR, 'root3', 'egg.nc'),
        os.path.join(ROOT_DIR, 'test_1.nc'),
        os.path.join(ROOT_DIR, 'test_2.yml'),
        os.path.join(ROOT_DIR, 'root4', 'egg.nc'),
    ]),
    ('*.nc', [
        os.path.join(ROOT_DIR, 'test.nc'),
        os.path.join(ROOT_DIR, 'root2', 'x.nc'),
        os.path.join(ROOT_DIR, 'root3', 'egg.nc'),
        os.path.join(ROOT_DIR, 'test_1.nc'),
        os.path.join(ROOT_DIR, 'root4', 'egg.nc'),
    ]),
    ('test*', [
        os.path.join(ROOT_DIR, 'test.nc'),
        os.path.join(ROOT_DIR, 'test_1.nc'),
        os.path.join(ROOT_DIR, 'test_2.yml'),
    ]),
    ('*.yml', [
        os.path.join(ROOT_DIR, 'egg.yml'),
        os.path.join(ROOT_DIR, 'test_2.yml'),
    ]),
    ('egg.nc*', [
        os.path.join(ROOT_DIR, 'root3', 'egg.nc'),
        os.path.join(ROOT_DIR, 'root4', 'egg.nc'),
    ]),
]


@pytest.mark.parametrize('pattern,output', PATTERNS_FOR_ALL_ANCESTORS)
@mock.patch('esmvaltool.diag_scripts.shared.io.os.walk', autospec=True)
def test_get_all_ancestor_files(mock_walk, pattern, output):
    """Test retrieving of ancestor files."""
    input_dirs = [
        [
            (ROOT_DIR, ['dir', '__pycache__'], ['test.nc', 'egg.yml']),
            (os.path.join(ROOT_DIR, 'root2'), ['d'], ['x.nc', 'y.png']),
            (os.path.join(ROOT_DIR, 'root3'), [], ['egg.nc']),
        ],
        [
            (ROOT_DIR, ['dir', '__pycache__'], ['test_1.nc', 'test_2.yml']),
            (os.path.join(ROOT_DIR, 'root4'), ['d2'], ['egg.nc']),
        ],
    ]
    mock_walk.side_effect = input_dirs
    files = io.get_all_ancestor_files(CFG, pattern=pattern)
    assert files == output


PATTERNS_FOR_SINGLE_ANCESTOR = [
    ([], None, True),
    (['I/am/a/cool/file.nc'], 'I/am/a/cool/file.nc', False),
    (['I/am/a/cool/file.nc', 'oh/no/file_2.nc'], 'I/am/a/cool/file.nc', True),
]


@pytest.mark.parametrize('files,output,logger', PATTERNS_FOR_SINGLE_ANCESTOR)
@mock.patch.object(io, 'get_all_ancestor_files', autospec=True)
@mock.patch.object(io, 'logger', autospec=True)
def test_get_ancestor_file(mock_logger, mock_get_all_ancestors, files, output,
                           logger):
    """Test retrieving of single ancestor file."""
    mock_get_all_ancestors.return_value = files
    returned_file = io.get_ancestor_file(CFG, pattern='*')
    assert returned_file == output
    if logger:
        mock_logger.warning.assert_called()
    else:
        mock_logger.warning.assert_not_called()


LONG_NAME = 'Loooong name'
SHORT_NAME = 'var'
STANDARD_NAME = 'air_temperature'
UNITS = 'K'


@mock.patch.object(io, 'get_all_ancestor_files', autospec=True)
@mock.patch.object(io, 'logger', autospec=True)
@mock.patch('esmvaltool.diag_scripts.shared.io.iris.load_cube', autospec=True)
@mock.patch('esmvaltool.diag_scripts.shared.io.os.walk', autospec=True)
def test_netcdf_to_metadata(mock_walk, mock_load_cube, mock_logger,
                            mock_get_all_ancestors):
    """Test cube to metadata."""
    attrs = [
        {
            'dataset': 'model',
            'filename': 'path/to/model1.nc',
            'project': 'CMIP42',
        },
        {
            'dataset': 'model',
            'filename': 'path/to/model1.yml',
            'project': 'CMIP42',
        },
        {
            'dataset': 'model',
            'filename': 'path/to/model2.nc',
        },
        {
            'dataset': 'model',
            'filename': 'path/to/model3.nc',
            'project': 'CMIP42',
        },
    ]
    var_attrs = [
        {
            'long_name': LONG_NAME,
            'var_name': SHORT_NAME,
            'units': UNITS,
        },
        {
            'long_name': LONG_NAME,
            'var_name': SHORT_NAME,
            'units': UNITS,
        },
        {
            'long_name': LONG_NAME,
            'var_name': SHORT_NAME,
        },
        {
            'long_name': LONG_NAME,
            'var_name': SHORT_NAME,
            'standard_name': STANDARD_NAME,
            'units': UNITS,
        },
    ]
    cubes = [
        iris.cube.Cube(0, attributes=attrs[0], **var_attrs[0]),
        iris.cube.Cube(0, attributes=attrs[2], **var_attrs[2]),
        iris.cube.Cube(0, attributes=attrs[3], **var_attrs[3]),
    ]
    walk_output = [
        ('path/to', [], ['model1.nc', 'model1.yml']),
        ('path/to', ['d'], ['model2.nc', 'model3.nc']),
    ]
    output = deepcopy([{**attrs[i], **var_attrs[i]} for i in (0, 3)])
    for out in output:
        out['short_name'] = out.pop('var_name')
    mock_get_all_ancestors.return_value = [a['filename'] for a in attrs]
    mock_walk.return_value = walk_output
    for root in (None, '*'):
        mock_load_cube.side_effect = cubes
        metadata = io.netcdf_to_metadata({}, pattern=root, root=root)
        assert metadata == output
        mock_logger.warning.assert_called()
        mock_logger.reset_mock()


ATTRS = [
    {
        'dataset': 'a',
        'filename': 'path/to/model1.nc',
        'project': 'CMIP42',
    },
    {
        'dataset': 'b',
        'filename': 'path/to/model2.nc',
        'project': 'CMIP42',
    },
    {
        'dataset': 'c',
        'filename': 'path/to/model3.nc',
    },
    {
        'dataset': 'd',
        'filename': 'path/to/model4.nc',
        'project': 'CMIP42',
    },
]
VAR_ATTRS = [
    {
        'long_name': LONG_NAME,
        'var_name': SHORT_NAME,
        'units': UNITS,
    },
    {
        'long_name': LONG_NAME,
        'var_name': SHORT_NAME,
        'units': UNITS,
    },
    {
        'long_name': LONG_NAME,
        'var_name': SHORT_NAME,
    },
    {
        'long_name': LONG_NAME,
        'var_name': SHORT_NAME,
        'standard_name': STANDARD_NAME,
        'units': UNITS,
    },
]
CUBES = [
    iris.cube.Cube(0, attributes=ATTRS[i], **VAR_ATTRS[i]) for i in range(4)
]
OUTPUT = [[CUBES[i], ATTRS[i]['filename']] for i in range(4)]
OUTPUT[2] = None
METADATA_TO_NETDCF = zip(ATTRS, VAR_ATTRS, CUBES, OUTPUT)


@pytest.mark.parametrize('attrs,var_attrs,cube,output', METADATA_TO_NETDCF)
@mock.patch.object(io, 'iris_save', autospec=True)
@mock.patch.object(io, 'logger', autospec=True)
def test_metadata_to_netcdf(mock_logger, mock_save, attrs, var_attrs, cube,
                            output):
    """Test metadata to cube."""
    wrong_name = 'I_am_an_invalid_standard_name'
    metadata = deepcopy({**attrs, **var_attrs})
    metadata['short_name'] = metadata.pop('var_name')
    if metadata['dataset'] == 'a':
        metadata['standard_name'] = wrong_name
    io.metadata_to_netcdf(cube, metadata)
    if metadata.get('standard_name', '') == wrong_name:
        mock_logger.debug.assert_called()
    else:
        mock_logger.debug.assert_not_called()
    if output is None:
        mock_logger.error.assert_called()
        assert not mock_save.called
    else:
        mock_logger.error.assert_not_called()
        assert mock_save.call_args_list == [mock.call(*output)]


PATH = 'path/to/super/cube'
VAR_ATTRS_NEW = [
    {
        'long_name': 'I do not have units :(',
        'short_name': 'sad',
    },
    {
        'long_name': 'Long name',
        'short_name': 'var',
        'units': '1',
    },
    {
        'short_name': SHORT_NAME,
        'long_name': LONG_NAME,
        'standard_name': STANDARD_NAME,
        'units': UNITS,
    },
]
ATTRS_NEW = [
    {},
    {},
    {
        'test': '123',
        'answer': 42,
    },
]
ATTRIBUTES_FOR_1D_CUBE = zip(VAR_ATTRS_NEW, ATTRS_NEW)


@pytest.mark.parametrize('var_attrs,attrs', ATTRIBUTES_FOR_1D_CUBE)
@mock.patch.object(io, 'iris_save', autospec=True)
@mock.patch.object(io, 'logger', autospec=True)
def test_save_1d_data(mock_logger, mock_save, var_attrs, attrs):
    """Test saving of 1 dimensional data."""
    coord_name = 'inclination'
    data = [
        np.ma.masked_invalid([1.0, np.nan, -1.0]),
        np.arange(5.0),
    ]
    coords = [
        iris.coords.DimCoord(np.ma.arange(3.0), long_name=coord_name),
        iris.coords.DimCoord(np.ma.arange(5.0), long_name=coord_name),
    ]
    cubes = OrderedDict([
        ('model1',
         iris.cube.Cube(
             data[0],
             var_name='xy',
             units='kg',
             attributes={'hi': '!'},
             dim_coords_and_dims=[(coords[0], 0)])),
        ('model2',
         iris.cube.Cube(
             data[1],
             var_name='zr',
             units='1',
             attributes={},
             dim_coords_and_dims=[(coords[1], 0)])),
    ])
    dataset_dim = iris.coords.AuxCoord(list(cubes.keys()), long_name='dataset')
    output_data = np.ma.masked_invalid([[1.0, np.nan, -1.0, np.nan, np.nan],
                                        [0.0, 1.0, 2.0, 3.0, 4.0]])
    output_dims = [(dataset_dim, 0), (coords[1], 1)]

    # Without cubes
    io.save_1d_data({}, PATH, coord_name, var_attrs, attrs)
    mock_logger.error.assert_called()
    assert not mock_save.called
    mock_logger.reset_mock()
    mock_save.reset_mock()

    # With cubes
    io.save_1d_data(cubes, PATH, coord_name, var_attrs, attrs)
    iris_var_attrs = deepcopy(var_attrs)
    iris_var_attrs['var_name'] = iris_var_attrs.pop('short_name')
    new_cube = iris.cube.Cube(
        output_data,
        aux_coords_and_dims=output_dims,
        attributes={
            **attrs, 'filename': PATH
        },
        **iris_var_attrs)
    if 'units' not in var_attrs:
        mock_logger.error.assert_called()
        assert not mock_save.called
    else:
        mock_logger.error.assert_not_called()
        assert mock_save.call_args_list == [mock.call(new_cube, PATH)]


@mock.patch.object(io, 'iris', autospec=True)
@mock.patch.object(io, 'logger', autospec=True)
def test_iris_save(mock_logger, mock_iris):
    """Test iris save function."""
    cube = iris.cube.Cube(0)
    io.iris_save(cube, PATH)
    mock_iris.save.assert_called_once_with(cube, PATH)
    mock_logger.info.assert_called_once()


AUX_COORDS = [
    None,
    None,
    iris.coords.AuxCoord([2, 3, 5], long_name='Primes!'),
]
ATTRIBUTES_FOR_SCALAR_CUBE = zip(VAR_ATTRS_NEW, ATTRS_NEW, AUX_COORDS)


@pytest.mark.parametrize('var_attrs,attrs,aux_coord',
                         ATTRIBUTES_FOR_SCALAR_CUBE)
@mock.patch.object(io, 'iris_save', autospec=True)
@mock.patch.object(io, 'logger', autospec=True)
def test_save_scalar_data(mock_logger, mock_save, var_attrs, attrs, aux_coord):
    """Test saving of scalar data."""
    data = OrderedDict([
        ('model1', np.nan),
        ('model2', 1.0),
        ('model3', 3.14),
    ])
    dataset_dim = iris.coords.AuxCoord(list(data.keys()), long_name='dataset')
    output_data = np.ma.masked_invalid([np.nan, 1.0, 3.14])

    # Without data
    io.save_scalar_data({}, PATH, var_attrs)
    mock_logger.error.assert_called()
    assert not mock_save.called
    mock_logger.reset_mock()
    mock_save.reset_mock()

    # With data
    io.save_scalar_data(data, PATH, var_attrs, aux_coord, attrs)
    iris_var_attrs = deepcopy(var_attrs)
    iris_var_attrs['var_name'] = iris_var_attrs.pop('short_name')
    new_cube = iris.cube.Cube(
        output_data,
        aux_coords_and_dims=[(dataset_dim, 0)],
        attributes={
            **attrs, 'filename': PATH
        },
        **iris_var_attrs)
    if aux_coord is not None:
        new_cube.add_aux_coord(aux_coord, 0)
    if 'units' not in var_attrs:
        mock_logger.error.assert_called()
        assert not mock_save.called
    else:
        mock_logger.error.assert_not_called()
        assert mock_save.call_args_list == [mock.call(new_cube, PATH)]
