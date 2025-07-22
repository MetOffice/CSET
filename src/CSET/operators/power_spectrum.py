# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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

"""Operator to calculate power spectrum from a 2D cube or CubeList."""

import iris
import numpy as np
import scipy.fft as fft
import warnings

def calculate_power_spectrum(
    cube: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube:
    """Power spectrum is calculated.

    Arguments
    ---------
    cube: iris.cube.Cube | iris.cube.CubeList
        Cube(s) to filter

    Returns
    -------
    iris.cube.Cube

    Raises
    ------
    ValueError
        If the constraint doesn't produce a single cube.
    """
    # Calculate power spectra using discrete cosine transform
    power_spectrum=DCT_ps(cube.data)

    return power_spectrum

#####################################################################
def DCT_ps(y_2d):

    # Get max dims
    Ny,Nx=y_2d.shape

    alpha_matrix=create_alpha_matrix(Ny,Nx)

    # Do DCT transformation and convert to dask
    fkk=fft.dctn(y_2d)

    #Normalize
    fkk=fkk/np.sqrt(Ny*Nx)

    # do variance of spectral coeff
    sigma_2=fkk**2/Nx/Ny

    #Max coefficient
    Nmin=min(Nx-1,Ny-1)

    ps=np.zeros(Nmin)
    # Group elipses of alphas into the same wavenumber k/Nmin
    for k in range(1,Nmin+1):
        alpha=k/Nmin
        alpha_p1=(k+1)/Nmin
        # Sum up elements matching k
        mask_k=np.where((alpha_matrix >=alpha) & (alpha_matrix < alpha_p1))
        ps[k-1]=np.sum(sigma_2[mask_k])

    return ps

#####################################################################
def create_alpha_matrix(Ny,Nx):

    I=np.arange(Nx)+1
    for n in range(1,Ny): 
        I=np.append(I,np.arange(Nx)+1)

    I.resize(Ny,Nx)

    J=np.arange(Ny)+1
    for n in range(1,Nx): 
        J=np.append(J,np.arange(Ny)+1)     

    J.resize(Nx,Ny)
    J=np.transpose(J)

    alpha_matrix=(np.sqrt(I*I/Nx**2+J*J/Ny**2))

    return alpha_matrix


#                     END OF PROGRAM                                     #
##########################################################################
if __name__ == '__main__':
    
    main()


