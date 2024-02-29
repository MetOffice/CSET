# Copyright 2022 Met Office and contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import iris
import iris.analysis
import numpy as np
import scipy.ndimage as ndimage
from CSET.operators.diagnostics.constants import M_IN_KM, CELL_CONNECTIVITY
from CSET.operators.diagnostics.utils import guess_bounds, get_spatial_coords, get_non_spatial_coords

def _neighbours(L, P, NPIXELS, NLINES, method=1):
    """
    Returns the neighbours of a pixel, either just neighbours to the side \
    (method 0) or including diagnonal neigbours (method 1)
    """
    # Returns neighbours of pixel (L, P) on line L and L-1 only
    if method==0:
        # Only connected by sides (4 neighbours)
        if L==0:
            if P==0:
                A = (np.array([0]), np.array([0]))
            else:
                A = (np.array([0, 0]), np.array([P-1, P]))
        elif P==0:
            A = (np.array([L-1, L]), np.array([0, 0]))
        else:
            A = (np.array([L-1, L, L]), np.array([P, P-1, P]))
    elif method==1:
        # Connected through diagonals (8 neighbours)
        if L==0:
            if P==0:
                A = (np.array([0]), np.array([0]))
            else:
                A = (np.array([0, 0]), np.array([P-1, P]))
        elif P==0:
            A = (np.array([L-1, L-1, L]), np.array([0, P+1, 0]))
        elif P==NPIXELS-1:
            A = (np.array([L-1, L-1, L, L]), np.array([P-1, P, P-1, P]))
        else:
            A = (np.array([L-1, L-1, L-1, L, L]), np.array([P-1, P, P+1,
                                                            P-1, P]))
    else:
        raise ValueError("Error: Method must be 0 or 1")

    return A

def _neighbours_flip(L, P, NPIXELS, NLINES, method=1):
    """
    Returns the neighbours of a pixel, either just neighbours to the side \
    (method 0) or including diagnonal neigbours (method 1)
    """
    # Returns neighbours of pixel (L, P) on line L and L+1 only
    if method==0:
        # Only connected by sides (4 neighbours)
        if L==NLINES-1:
            if P==NPIXELS-1:
                A = (np.array([L]), np.array([P]))
            else:
                A = (np.array([L, L]), np.array([P, P+1]))
        elif P==NPIXELS-1:
            A = (np.array([L, L+1]), np.array([P, P]))
        else:
            A = (np.array([L, L, L+1]), np.array([P, P+1, P]))
    elif method==1:
        # Connected through diagonals (8 neighbours)
        if L==NLINES-1:
            if P==NPIXELS-1:
                A = (np.array([L]), np.array([P]))
            else:
                A = (np.array([L, L]), np.array([P, P+1]))
        elif P==NPIXELS-1:
            A = (np.array([L, L+1, L+1]), np.array([P, P-1, P]))
        elif P==0:
            A = (np.array([L, L, L+1, L+1]), np.array([P, P+1, P, P+1]))
        else:
            A = (np.array([L, L, L+1, L+1, L+1]), np.array([P, P+1,
                                                            P-1, P, P+1]))
    else:
        raise ValueError("Error: Method must be 0 or 1")

    return A

def _connected_object_labelling_reading(bt, minarea, threshold, method=1,
                                       block_radius=3,
                                       missing_data_value=np.nan):
    """
    THIS BASIC CODE LOADS A SEVIRI IMAGE AND MAKES A BINARY IMAGE
    OUT OF BRIGHTNESS TEMPERATURES USING threshold.
    THE BINARY IMAGE IS THEN USED AS INPUT FOR LABELLING STORMS.
    ALGORITHM ON PAGE 37-39 HARALICK AND SHAPIRO.
    RESULT IS A STRUCT "M" CONTAINING STORMS "S" AND CELLS
    (LOCAL np.max/np.min) "C" AND A MATRIX "labelbt" LABELLING EACH
    REGION S AND A MATRIX "localnp.max" LABELLING EACH LOCAL np.max C
    TRY pcolor(M.labelbt) TO SEE REGIONS
    THEN LOOP THROUGH M.C TO ADD LOCATIONS OF LOCAL np.max/np.min
    LOOP THROUGH M.S TO REPLACE misval IN STORM PROPERTIES

    bt                 :: 2D vector of brightness temperatures
    np.minarea         :: np.minimum size threshold (number of pixels)
                          of feature
    threshold          :: brightness temperature threshold to distinguish
                          features from background
    method             :: (0) standard direct neighbours (1) include diagonals
    block_radius       :: to define square region around a value to check \
                          if it's a local np.maximum/np.minimum
    missing_data_value :: value assigned to missing data

    Returns the label matrix and a list of storms in the bt array
    """
    # These commented lines were replaced with the below to deal with
    # masked arrays (Chris Short)
    #binbt = 0*bt
    #binbt[np.where(bt>threshold)] = 1
    #binbt[np.where(bt<=threshold)] = 0

    # Apply the supplied threshold to the data to generate a binary array
    binbt = bt.copy()
    if np.ma.is_masked(binbt):
        # If the data is masked, replace any masked values with (threshold - 1)
        # thus guaranteeing they will be below the threshold and thus set to 0
        # below
        binbt = np.ma.filled(binbt, fill_value=(threshold - 1))
    # Set values above and below the threshold to 1 and 0, respectively
    indices_above = (binbt > threshold)
    indices_below = (binbt <= threshold)
    binbt[indices_above] = 1
    binbt[indices_below] = 0

    labelbt = 0*binbt

    NLINES = np.size(binbt, 0)
    NPIXELS = np.size(binbt, 1)

    newlabel = 1

    # First loop
    # Top-down (left-right) scan through binary array
    # First set of labels and equivalences assigned (eqtable)
    # Local max assigned if local maximum within blockradius
    # Local max used to indicate individual cells within a storm
    for L in range(0, NLINES):
        eqtable = np.zeros((100, 100))
        newline = []
        for P in range(0, NPIXELS):
            if binbt[L,P]==1:
                A = _neighbours(L, P, NPIXELS, NLINES, method=method)
                B = np.where(labelbt[A]>0)
                if np.size(B)==0:
                    NL = newlabel
                    newlabel = newlabel + 1
                else:
                    NL = np.min(labelbt[A[0][B], A[1][B]])
                    for X in range(0, np.size(B)):
                        if labelbt[A[0][B[0][X]]][A[1][B[0][X]]]!=NL:
                            if np.max(eqtable)==0:
                                eqtable[0][0] = NL
                                eqtable[0][1] = labelbt[A[0][B[0][X]], A[1][B[0][X]]]
                            else:
                                C = np.where(eqtable==labelbt[A[0][B[0][X]], A[1][B[0][X]]])
                                if np.size(C)==0:
                                    C = np.where(eqtable==NL)
                                    if np.size(C)==0:
                                        newline = np.min(np.where(eqtable[:][0]==0))
                                        eqtable[newline][0] = labelbt[A[0][B[0][X]],A[1][B[0][X]]]
                                        eqtable[newline][1] = NL
                                    else:
                                        for Y in range(0, np.size(C,1)):
                                            if eqtable[C[0][Y]][C[1][Y]]==NL:
                                                D = np.where(eqtable[C[0][Y]][:]==0)
                                                eqtable[C[0][Y]][np.min(D)] = labelbt[A[0][B[0][X]],A[1][B[0][X]]]
                                else:
                                    G = np.where(eqtable==NL)
                                    if np.size(G)==0:
                                        for Y in range(0, np.size(C,1)):
                                            if eqtable[C[0][Y]][C[1][Y]]==labelbt[A[0][B[0][X]],A[1][B[0][X]]]:
                                                D = np.where(eqtable[C[0][Y]][:]==0)
                                                eqtable[C[0][Y]][np.min(D)] = NL
                labelbt[L, P] = NL

        if np.max(eqtable)>0:
            eqtable[np.where(eqtable==0)] = np.max(labelbt) + 1
            eqlabel = np.zeros(100)
            for E in range(0, 100):
                eqlabel[E] = np.min(eqtable[E][:])
            for P in range(0, NPIXELS):
                if binbt[L, P]==1:
                    B = np.where(eqtable==labelbt[L, P])
                    if np.size(B)>0:
                        labelbt[L, P] = eqlabel[B[0][0]]

    # Second loop
    # Down-up (right-left) scan through label array to find equivalent labels
    # and set uniform label per region
    for L in range(NLINES-1, -1, -1):
        eqtable = np.zeros((100, 100))
        newline = []
        for P in range(NPIXELS-1, -1, -1):
            if labelbt[L,P]!=0:
                A = _neighbours_flip(L, P, NPIXELS, NLINES, method=method)
                B = np.where(labelbt[A]>0)
                NL = labelbt[L, P]
                for X in range(0, np.size(B)):
                    if labelbt[A[0][B[0][X]]][A[1][B[0][X]]]!=NL:
                        if np.max(eqtable)==0:
                            eqtable[0][0] = NL
                            eqtable[0][1] = labelbt[A[0][B[0][X]], A[1][B[0][X]]]
                        else:
                            C = np.where(eqtable==labelbt[A[0][B[0][X]], A[1][B[0][X]]])
                            if np.size(C)==0:
                                C = np.where(eqtable==NL)
                                if np.size(C)==0:
                                    newline = np.min(np.where(eqtable[:][0]==0))
                                    eqtable[newline][0] = labelbt[A[0][B[0][X]], A[1][B[0][X]]]
                                    eqtable[newline][1] = NL
                                else:
                                    for Y in range(0, np.size(C,1)):
                                        if eqtable[C[0][Y]][C[1][Y]]==NL:
                                            D = np.where(eqtable[C[0][Y]][:]==0)
                                            eqtable[C[0][Y]][np.min(D)] = labelbt[A[0][B[0][X]], A[1][B[0][X]]]
                            else:
                                G = np.where(eqtable==NL)
                                if np.size(G)==0:
                                    for Y in range(0, np.size(C,1)):
                                        if eqtable[C[0][Y]][C[1][Y]]==labelbt[A[0][B[0][X]], A[1][B[0][X]]]:
                                            D = np.where(eqtable[C[0][Y]][:]==0)
                                            eqtable[C[0][Y]][np.min(D)] = NL

        if np.max(eqtable)>0:
            eqtable[np.where(eqtable==0)] = np.max(labelbt) + 1
            eqlabel = np.zeros(100)
            for E in range(0, 100):
                eqlabel[E] = np.min(eqtable[E][:])
            for P in range(0, NPIXELS):
                if binbt[L, P]==1:
                    B = np.where(eqtable==labelbt[L, P])
                    if np.size(B)>0:
                        labelbt[L, P] = eqlabel[B[0][0]]

    maxnum = 0
    for ii in range(1, int(np.max(labelbt))+1):
        ind = np.where(labelbt==ii)
        if 0 < np.size(ind)/2 < minarea:
            labelbt[ind] = 0
        elif np.size(ind)/2 >= minarea:
            maxnum = maxnum + 1

    return labelbt

def _connected_object_labelling(data, threshold=0.0, min_size=1, connectivity=1):
    '''
    Finds connected objects in an input array and assigns them unique labels.

    Arguments:

    * **data** - a :class:`numpy.ndarray` array in which to label objects.

    Keyword arguments:

    * **threshold** - if supplied, only regions where the input data exceeds \
                      the threshold will be considered when searching for \
                      connected objects.
    * **min_size** - minimum size in grids points for connected objects. Must \
                     be an integer >= 1.
    * **connectivity** - given a particular grid point, all grid points up to \
                         a squared distance of connectivity away are considered \
                         neighbours. Connectivity may range from 1 (only direct \
                         neighbours are considered) to :attr:`data.ndim`.

    Returns:

    * **label_array** - an integer array where each unique object in the input \
                        array has a unique label in the returned array.
    * **num_objects** - the number of objects found.
    '''
    # Apply the supplied threshold to the data to generate a binary array
    binary_data = data.copy()
    if np.ma.is_masked(binary_data):
        # If the data is masked, replace any masked values with (threshold - 1)
        # thus guaranteeing they will be below the threshold and thus set to 0
        # below
        binary_data = np.ma.filled(binary_data, fill_value=(threshold - 1))
    # Set values above and below the threshold to 1 and 0, respectively
    indices_above = (binary_data > threshold)
    indices_below = (binary_data <= threshold)
    binary_data[indices_above] = 1
    binary_data[indices_below] = 0

    # Construct a structuring element that defines how the neighbours of
    # a grid point are assigned
    structure_element = ndimage.morphology.generate_binary_structure(
        data.ndim, connectivity)

    # Label distinct (connected) objects in the binary array
    label_array, num_objects = ndimage.measurements.label(
        binary_data,
        structure=structure_element)

    # Throw away any objects smaller than min_size
    if min_size < 1:
        raise ValueError('"min_size" must be 1 or greater')
    elif min_size > 1:
        labels = np.unique(label_array)
        # Discard the background (which will be labelled as 0)
        labels = labels[(labels > 0)]
        # Loop over distinct objects
        for label in labels:
            # Find the indices of the grid points comprising this object
            indices = np.where(label_array == label)
            # If this object is smaller than min_size, set it as background
            if indices[0].size < min_size:
                label_array[indices] = 0
                num_objects -= 1

    return label_array, num_objects

def _find_cells(cube, threshold=0.0, area_threshold=0.0, connectivity=1):
    '''
    Finds connected objects (i.e. cells) in spatial slices of a given \
    :class:`iris.cube.Cube`.

    Arguments:

    * **cube** - an input :class:`iris.cube.Cube` object.

    Keyword arguments:

    * **threshold** - if supplied, only regions where the input data exceeds \
                      the threshold will be considered when identifying cells.
    * **area_threshold** - minimum area in km^2 that cells must have.
    * **connectivity** - given a particular grid point, all grid points up to a \
                         squared distance of connectivity away are considered \
                         neighbours. Connectivity may range from 1 (only \
                         direct neighbours are considered) to \
                         :attr:`cube.data.ndim`.

    Returns:

    * **cells** - a :class:`iris.cube.CubeList` of \
                  :class:`iris.cube.Cube` objects, each one corresponding to \
                  an identified cell.
    '''
    # Flag whether to use old cell labelling code from Reading
    # TODO To be removed once testing of new code is complete
    use_old_code = False

    # Convert input area threshold from km^2 to m^2
    area_threshold = (float(M_IN_KM)**2) * area_threshold

    # Get x, y coordinates of input cube
    x_coord, y_coord = get_spatial_coords(cube)
    x, y = iris.analysis.cartography.get_xy_grids(cube)

    # Guess x, y coordinate bounds
    cube = guess_bounds(cube)

    # Loop over 2D spatial slices of the input cube and find cells in each
    # slice
    grid_areas = None
    cells = iris.cube.CubeList()
    coords = get_non_spatial_coords(cube)
    for slc in cube.slices_over(coords):
        if grid_areas is None:
            # Area of grid cells, in m^2
            grid_areas = iris.analysis.cartography.area_weights(slc)

        # Store a list of the non-spatial coordinates for this slice
        aux_coords = [(coord, []) for coord in
                      get_non_spatial_coords(slc)]

        # Find and label cells
        if use_old_code:
            # Call connected object labelling function from Reading
            cell_label_array = _connected_object_labelling_reading(slc.data,
                                                                0.0,
                                                                threshold,
                                                                method=1)
        else:
            # Call connected object labelling function based on
            # scipy.ndimage.measurements.label
            cell_label_array, _ = _connected_object_labelling(
                slc.data,
                threshold=threshold,
                min_size=1,
                connectivity=connectivity)

        # Get a list of unique cell labels
        cell_labels = np.unique(cell_label_array)
        # Discard background (which has a label of 0)
        cell_labels = cell_labels[(cell_labels > 0)]
        # Loop over cell and store their properties
        for cell_label in cell_labels:
            # Find the indices of the grid points comprising this cell
            cell_indices = np.where(cell_label_array == cell_label)
            cell_x = x[cell_indices]
            cell_y = y[cell_indices]
            cell_values = slc.data[cell_indices]
            cell_grid_areas = grid_areas[cell_indices]

            # There should not be any masked data present in cells!
            if np.ma.is_masked(cell_values):
                raise ValueError("Masked data found in cell {0:d}"
                                 .format(cell_label))

            # If cell area is less than area_threshold, discard it
            # (by setting its label to the background value)
            cell_area = np.sum(cell_grid_areas, dtype=np.float64)
            if cell_area < area_threshold:
                cell_label_array[cell_indices] = 0
                continue

            # Estimate cell centre position
            # TODO Is there a better way of doing this? C.O.M?
            cell_centre = (np.mean(cell_x, dtype=np.float64),
                           np.mean(cell_y, dtype=np.float64))
            # Area-weighted mean value in cell
            cell_mean = (np.sum((cell_grid_areas * cell_values),
                                dtype=np.float64)
                         / cell_area)
            # Convert cell area from m^2 to km^2...
            cell_area /= (float(M_IN_KM)**2)
            # ...and then cell effective radius in km
            cell_radius = np.sqrt(cell_area / np.pi)

            # Create an Iris cube to store this cell
            cell_cube = iris.cube.Cube(
                cell_values,
                long_name="{:s} cell".format(cube.name()),
                units=cube.units,
                attributes=cube.attributes,
                cell_methods=cube.cell_methods,
                aux_coords_and_dims=aux_coords)

            # Set up x, y coordinates describing the grid points in the cell...
            cell_x_coord = iris.coords.AuxCoord(
                cell_x,
                standard_name=x_coord.standard_name,
                long_name=x_coord.long_name,
                units=x_coord.units,
                bounds=None,
                attributes=x_coord.attributes,
                coord_system=x_coord.coord_system)
            cell_y_coord = iris.coords.AuxCoord(
                cell_y,
                standard_name=y_coord.standard_name,
                long_name=y_coord.long_name,
                units=y_coord.units,
                bounds=None,
                attributes=y_coord.attributes,
                coord_system=y_coord.coord_system)
            # ...and add them to the cell cube
            cell_cube.add_aux_coord(cell_x_coord, 0)
            cell_cube.add_aux_coord(cell_y_coord, 0)

            # Set up a coordinate describing the areas of grid cells in
            # the cell object...
            cell_grid_area_coord = iris.coords.AuxCoord(cell_grid_areas,
                                                        long_name="grid_areas",
                                                        units="m2")
            #...and add it to the cell cube
            cell_cube.add_aux_coord(cell_grid_area_coord, 0)

            # Finally add some attriubtes to the cube that describe some
            # useful information about the cell
            cell_cube.attributes["centre"] = cell_centre
            cell_cube.attributes["area_in_km2"] = cell_area
            cell_cube.attributes["effective_radius_in_km"] = cell_radius
            cell_cube.attributes["mean_value"] = cell_mean
            
            cells.append(cell_cube)

    return cells

def cell_attribute_histogram(cube, attribute, bin_edges, bin_centres=None,
                             threshold=0.0, area_threshold=0.0):
    bin_edges = np.asarray(bin_edges)
    if bin_centres is None:
        bin_centres = 0.5 * (bin_edges[1:] + bin_edges[:-1])
    else:
        bin_centres = np.asarray(bin_centres)

    # Check that the number of bin edges and centres is correct
    if bin_edges.size != (bin_centres.size + 1):
        raise ValueError("Number of bin edges must be one greater than the "
                         "number of bin centres.")
    
    # Express histogram bins as an Iris coordinate
    bins_as_coord = iris.coords.DimCoord(
        bin_centres,
        long_name=attribute,
        units=cube.units,
        coord_system=None,
        bounds=np.column_stack((bin_edges[0:-1], bin_edges[1:])))
    
    # Loop over 2D spatial slices in cube, find cells and construct histogram
    data_min, data_max = None, None
    hist_cube = iris.cube.CubeList()
    coords = get_non_spatial_coords(cube)
    
    for slc in cube.slices_over(coords):
        # Identify connected cells in this spatial slice
        cells = _find_cells(
            slc,
            threshold=threshold,
            area_threshold=area_threshold,
            connectivity=CELL_CONNECTIVITY)
    
        if cells:
                # Extract values of the desired cell attribute
                cell_attributes = [cell.attributes[attribute] for cell in cells]
        
                # Store the minimum/maximum values of the cell attribute
                if data_min is None or np.min(cell_attributes) < data_min:
                    data_min = np.min(cell_attributes)
                if data_max is None or np.max(cell_attributes) > data_max:
                    data_max = np.max(cell_attributes)

                # Construct a histogram of the desired cell attribute
                hist, _ = np.histogram(cell_attributes, bin_edges)
        else:
                # Assign zeros to all bins
                hist = np.zeros(bin_centres.size).astype(np.int64)

        # Get a list of the non-spatial coordinates for this slice
        aux_coords = [(coord, []) for coord in
                        get_non_spatial_coords(slc)]

        # Construct a cube to hold the cell statistic histogram for this slice
        hist_slc = iris.cube.Cube(hist,
                            long_name=("{0:s} cell {1:s} histogram"
                                        .format(slc.name(), attribute)),
                            units="no_unit",
                            attributes=slc.attributes,
                            cell_methods=slc.cell_methods,
                            dim_coords_and_dims=[(bins_as_coord, 0)],
                            aux_coords_and_dims=aux_coords)
        
        hist_cube.append(hist_slc)
        
    # If the bins did not fully enclose the data, they will need adjusting
    if data_min is not None and data_max is not None:
        if (data_min < np.min(bin_edges)) or (data_max > np.max(bin_edges)):
            msg = ("Bins do not fully enclose data. Adjust them. Cell {0:s} "
                   "(min, max)=({1:.4f}, {2:.4f}), bin edge "
                   "(min, max)=({3:.4f}, {4:.4f})".format(attribute,
                                                          data_min,
                                                          data_max,
                                                          np.min(bin_edges),
                                                          np.max(bin_edges)))
            raise ValueError(msg)
    
    # Merge all histograms into a single cube
    hist_cube = hist_cube.merge_cube()
    
    return hist_cube

def compute_cell_stats(cubes, threshold, BIN_EDGES, cell_attribute):
    for cube in cubes:
        cube.var_name = None
        for coord in cube.coords():
            coord.var_name = None
    
    
    lcube = [cell_attribute_histogram(
        cube, 
        cell_attribute, 
        BIN_EDGES, 
        threshold=threshold
        ) for cube in cubes]
    
    return lcube
