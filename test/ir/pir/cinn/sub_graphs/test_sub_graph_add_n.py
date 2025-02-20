# Copyright (c) 2024 PaddlePaddle Authors. All Rights Reserved.
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

# repo: PaddleDetection
# model: configs^cascade_rcnn^cascade_rcnn_r50_fpn_1x_coco_single_dy2st_train
# api:paddle.tensor.math.add_n
from base import *  # noqa: F403

from paddle.static import InputSpec


class AddNCase(paddle.nn.Layer):
    def __init__(self):
        super().__init__()

    def forward(
        self,
        var_0,  # (shape: [], dtype: paddle.float32, stop_gradient: False)
        var_1,  # (shape: [], dtype: paddle.float32, stop_gradient: False)
        var_2,  # (shape: [], dtype: paddle.float32, stop_gradient: False)
        var_3,  # (shape: [], dtype: paddle.float32, stop_gradient: False)
        var_4,  # (shape: [], dtype: paddle.float32, stop_gradient: False)
        var_5,  # (shape: [], dtype: paddle.float32, stop_gradient: False)
        var_6,  # (shape: [], dtype: paddle.float32, stop_gradient: False)
        var_7,  # (shape: [], dtype: paddle.float32, stop_gradient: False)
    ):
        var_8 = paddle.tensor.math.add_n(
            [var_6, var_7, var_0, var_1, var_2, var_3, var_4, var_5]
        )
        return var_8


class TestAddN(TestBase):
    def init(self):
        self.input_specs = [
            InputSpec(
                shape=(-1,),
                dtype=paddle.float32,
                name=None,
                stop_gradient=False,
            ),
            InputSpec(
                shape=(-1,),
                dtype=paddle.float32,
                name=None,
                stop_gradient=False,
            ),
            InputSpec(
                shape=(-1,),
                dtype=paddle.float32,
                name=None,
                stop_gradient=False,
            ),
            InputSpec(
                shape=(-1,),
                dtype=paddle.float32,
                name=None,
                stop_gradient=False,
            ),
            InputSpec(
                shape=(-1,),
                dtype=paddle.float32,
                name=None,
                stop_gradient=False,
            ),
            InputSpec(
                shape=(-1,),
                dtype=paddle.float32,
                name=None,
                stop_gradient=False,
            ),
            InputSpec(
                shape=(-1,),
                dtype=paddle.float32,
                name=None,
                stop_gradient=False,
            ),
            InputSpec(
                shape=(-1,),
                dtype=paddle.float32,
                name=None,
                stop_gradient=False,
            ),
        ]
        self.inputs = (
            paddle.rand(shape=[1], dtype=paddle.float32),
            paddle.rand(shape=[1], dtype=paddle.float32),
            paddle.rand(shape=[1], dtype=paddle.float32),
            paddle.rand(shape=[1], dtype=paddle.float32),
            paddle.rand(shape=[1], dtype=paddle.float32),
            paddle.rand(shape=[1], dtype=paddle.float32),
            paddle.rand(shape=[1], dtype=paddle.float32),
            paddle.rand(shape=[1], dtype=paddle.float32),
        )
        self.net = AddNCase
        self.with_train = False
        self.atol = 1e-8


if __name__ == '__main__':
    unittest.main()
