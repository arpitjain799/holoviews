"""
Implements downsampling algorithms for large 1D datasets.

The algorithms implemented in this module have been adapted from
https://github.com/predict-idlab/plotly-resampler and are reproduced
along with the original license: 

MIT License

Copyright (c) 2022 Jonas Van Der Donckt, Jeroen Van Der Donckt, Emiel Deprost.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import math

import numpy as np
import param

try:
    from numba import njit
except:
    njit = lambda func: func

from .resampling import ResamplingOperation1D

@njit
def _argmax_area(prev_x, prev_y, avg_next_x, avg_next_y, x_bucket, y_bucket):
    """Vectorized triangular area argmax computation.
    Parameters
    ----------
    prev_x : float
        The previous selected point is x value.
    prev_y : float
        The previous selected point its y value.
    avg_next_x : float
        The x mean of the next bucket
    avg_next_y : float
        The y mean of the next bucket
    x_bucket : np.ndarray
        All x values in the bucket
    y_bucket : np.ndarray
        All y values in the bucket
    Returns
    -------
    int
        The index of the point with the largest triangular area.
    """
    return np.abs(
        x_bucket * (prev_y - avg_next_y)
        + y_bucket * (avg_next_x - prev_x)
        + (prev_x * avg_next_y - avg_next_x * prev_y)
    ).argmax()

@njit
def _lttb(x, y, n_out):
    """
    Downsample the data using the LTTB algorithm (python implementation).

    Args:
        x (np.ndarray): The x-values of the data.
        y (np.ndarray): The y-values of the data.
        n_out (int): The number of output points.
    Returns:
        np.array: The indexes of the selected datapoints.
    """
    # Bucket size. Leave room for start and end data points
    block_size = (y.shape[0] - 2) / (n_out - 2)
    # Note this 'astype' cast must take place after array creation (and not with the
    # aranage() its dtype argument) or it will cast the `block_size` step to an int
    # before the arange array creation
    offset = np.arange(start=1, stop=y.shape[0], step=block_size).astype(np.int64)

    # Construct the output array
    sampled_x = np.empty(n_out, dtype="int64")
    sampled_x[0] = 0
    sampled_x[-1] = x.shape[0] - 1

    a = 0
    for i in range(n_out - 3):
        a = (
            _argmax_area(
                prev_x=x[a],
                prev_y=y[a],
                avg_next_x=np.mean(x[offset[i + 1] : offset[i + 2]]),
                avg_next_y=y[offset[i + 1] : offset[i + 2]].mean(),
                x_bucket=x[offset[i] : offset[i + 1]],
                y_bucket=y[offset[i] : offset[i + 1]],
            )
            + offset[i]
        )
        sampled_x[i + 1] = a

    # ------------ EDGE CASE ------------
    # next-average of last bucket = last point
    sampled_x[-2] = (
        _argmax_area(
            prev_x=x[a],
            prev_y=y[a],
            avg_next_x=x[-1],  # last point
            avg_next_y=y[-1],
            x_bucket=x[offset[-2] : offset[-1]],
            y_bucket=y[offset[-2] : offset[-1]],
        )
        + offset[-2]
    )
    return sampled_x


def _nth_point(x, y, n_out):
    """
    Downsampling by selecting every n-th datapoint

    Args:
        x (np.ndarray): The x-values of the data.
        y (np.ndarray): The y-values of the data.
        n_out (int): The number of output points.
    Returns:
        np.array: The indexes of the selected datapoints.
    """
    n_samples = len(s)
    return np.arange(0, n_samples, max(1, math.ceil(n_samples / n_out)))


_ALGORITHMS = {
    'lttb': _lttb,
    'nth': _nth_point
}

class downsample1d(ResamplingOperation1D):
    """
    Implements downsampling of a regularly sampled 1D dataset.

    Supports multiple algorithms:

        - `lttb`: Largest Triangle Three Buckets downsample algorithm
        - `nth`: Selects every n-th point.
    """

    algorithm = param.Selector(default='lttb', objects=['lttb', 'nth'])

    def _process(self, element, key=None):
        if self.p.x_range:
            element = element[slice(*self.p.x_range)]
        if len(element) <= self.p.width:
            return element
        xs, ys = (element.dimension_values(i) for i in range(2))
        if ys.dtype == np.bool_:
            ys = ys.astype(np.int8)
        downsample = _ALGORITHMS[self.p.algorithm]
        samples = downsample(xs, ys, self.p.width)
        return element.iloc[samples]
