# Copyright (c) ONNX Project Contributors
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import numpy as np

import onnx
from onnx.backend.test.case.base import Base
from onnx.backend.test.case.node import expect


# RMS normalization's reference implementation
def _rms_normalization(X, W, axis=-1, epsilon=1e-5):  # type: ignore
    shape = X.shape
    rank = len(shape)
    if axis < 0:
        # If axis = -1 and rank of X is 4,
        # the axis is changed to -1 + 4 = 3,
        # which means the last axis.
        axis = axis + rank

    # Parameter used to convert N-D tensor RMS normalization to equivalent 2-D matirx operations.
    row_number = np.prod(shape[:axis]).astype(np.int64)
    col_number = np.prod(shape[axis:]).astype(np.int64)

    # After reshaping input tensor X into a matrix,
    # RMS normalization is equivalent to conducting
    # standardization on each column vector (s.t. each
    # column has zero mean and unit variance).
    x_mat = np.reshape(X, (row_number, col_number))
    # This computes RMS for every x_mat's column.
    x_squared = np.power(x_mat, 2)
    x_squared_mean = np.sum(x_squared, axis=1, keepdims=True) / col_number
    rms = np.sqrt(x_squared_mean)
    rms_plus_epsilon = rms + epsilon
    rms_plus_epsilon_sqrt = np.sqrt(rms_plus_epsilon)
    rms_reciprocal = np.reciprocal(rms_plus_epsilon_sqrt)
    # Standardization step. y_mat is zero-mean and unit-variance.
    y_mat = x_mat * rms_reciprocal
    # Apply affine transform on normalization outcome. W is linear coefficient.
    Y = np.reshape(y_mat, shape) * W

    return Y


def calculate_normalized_shape(x_shape, axis):  # type: ignore
    rank = len(x_shape)
    if axis < 0:
        axis = axis + rank
    return x_shape[axis:]


class RMSNormalization(Base):
    @staticmethod
    def export() -> None:
        X = np.random.randn(2, 3, 4, 5).astype(np.float32)

        def case(axis: int) -> None:
            normalized_shape = calculate_normalized_shape(X.shape, axis)
            W = np.random.randn(*normalized_shape).astype(np.float32)
            Y = _rms_normalization(X, W, axis)

            node = onnx.helper.make_node(
                "RMSNormalization",
                inputs=["X", "W"],
                outputs=["Y"],
                axis=axis,
            )

            if axis < 0:
                name = f"test_rms_normalization_4d_axis_negative_{-axis}"
            else:
                name = f"test_rms_normalization_4d_axis{axis}"

            expect(node, inputs=[X, W], outputs=[Y], name=name)

        for i in range(len(X.shape)):
            case(i)
            case(i - len(X.shape))

    @staticmethod
    def export_default_axis() -> None:
        X = np.random.randn(2, 3, 4, 5).astype(np.float32)

        # Default axis in RMSNormalization is -1.
        normalized_shape = calculate_normalized_shape(X.shape, -1)
        W = np.random.randn(*normalized_shape).astype(np.float32)
        # Axis is default to -1 in the reference implementation.
        Y = _rms_normalization(X, W)

        # Not specifying axis attribute means -1.
        node = onnx.helper.make_node(
            "RMSNormalization",
            inputs=["X", "W"],
            outputs=["Y"],
        )

        expect(
            node,
            inputs=[X, W],
            outputs=[Y],
            name="test_rms_normalization_default_axis",
        )

    @staticmethod
    def export2d() -> None:
        X = np.random.randn(3, 4).astype(np.float32)

        def case(axis: int) -> None:
            normalized_shape = calculate_normalized_shape(X.shape, axis)
            W = np.random.randn(*normalized_shape).astype(np.float32)
            Y = _rms_normalization(X, W, axis=axis)

            node = onnx.helper.make_node(
                "RMSNormalization",
                inputs=["X", "W"],
                outputs=["Y"],
                axis=axis,
            )

            if axis < 0:
                name = f"test_rms_normalization_2d_axis_negative_{-axis}"
            else:
                name = f"test_rms_normalization_2d_axis{axis}"

            expect(node, inputs=[X, W], outputs=[Y], name=name)

        for i in range(len(X.shape)):
            case(i)
            case(i - len(X.shape))

    @staticmethod
    def export3d_epsilon() -> None:
        epsilon = 1e-1
        X = np.random.randn(2, 3, 5).astype(np.float32)

        def case(axis: int) -> None:
            normalized_shape = calculate_normalized_shape(X.shape, axis)
            W = np.random.randn(*normalized_shape).astype(np.float32)
            Y = _rms_normalization(X, W, axis, epsilon)
            node = onnx.helper.make_node(
                "RMSNormalization",
                inputs=["X", "W"],
                outputs=["Y"],
                axis=axis,
                epsilon=epsilon,
            )

            if axis < 0:
                name = f"test_rms_normalization_3d_axis_negative_{-axis}_epsilon"
            else:
                name = f"test_rms_normalization_3d_axis{axis}_epsilon"

            expect(node, inputs=[X, W], outputs=[Y], name=name)

        for i in range(len(X.shape)):
            case(i)
            case(i - len(X.shape))
