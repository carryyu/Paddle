# Copyright (c) 2023 PaddlePaddle Authors. All Rights Reserved.
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


import unittest

import numpy as np

import paddle
from paddle.fluid import core


def mmha_wrapper(
    x,
    bias,
    src_mask,
    sequence_lengths,
    rotary_tensor,
    beam_cache_offset,
    cache_kv_out,
    qkv_out_scale,
    out_linear_shift,
    out_linear_smooth,
    beam_size,
    rotary_emb_dims,
    mask_broadcast_num_heads,
    compute_bias,
    use_neox_rotary_style,
    out_linear_in_scale,
    quant_round_type,
    quant_max_bound,
    quant_min_bound,
):
    return paddle._C_ops.masked_multihead_attention_(
        x,
        bias,
        src_mask,
        sequence_lengths,
        rotary_tensor,
        beam_cache_offset,
        cache_kv_out,
        qkv_out_scale,
        out_linear_shift,
        out_linear_smooth,
        beam_size,
        rotary_emb_dims,
        mask_broadcast_num_heads,
        compute_bias,
        use_neox_rotary_style,
        out_linear_in_scale,
        quant_round_type,
        quant_max_bound,
        quant_min_bound,
    )


@unittest.skipIf(
    not core.is_compiled_with_cuda(), "core is not compiled with CUDA"
)
class TestMMHAOp(unittest.TestCase):
    def setUp(self):
        np.random.seed(0)
        self.bsz = 2
        self.cache_bsz = 2
        self.num_head = 6
        self.dim_head = 32
        self.beam_size = 1
        self.max_seq_len = 6
        self.sequence_length = 5

        self.x = np.random.uniform(
            -0.05, 0.05, [self.bsz, 3, self.num_head, self.dim_head]
        )
        self.x_int = np.random.randint(
            2, 10, size=(self.bsz, 3, self.num_head, self.dim_head)
        ).astype("int")

        self.bias = np.random.uniform(
            -0.05, 0.05, [3, self.num_head, self.dim_head]
        )
        self.src_mask = np.zeros([self.bsz, 1, 1, self.sequence_length + 1])

        self.sequence_lengths = None
        self.rotary_tensor = None
        self.beam_cache_offset = None

        self.cache_kv_out = np.random.uniform(
            -0.05,
            0.05,
            [
                2,
                self.cache_bsz,
                self.num_head,
                self.sequence_length,
                self.dim_head,
            ],
        )
        numpy_ones = np.zeros(
            [2, self.cache_bsz, self.num_head, 1, self.dim_head]
        )
        self.cache_kv_mmha_out = np.concatenate(
            (self.cache_kv_out, numpy_ones), axis=3
        )

        self.qkv_out_scale = np.random.uniform(
            -0.5, 1, [3, self.num_head, self.dim_head]
        )
        self.out_linear_shift = None
        self.out_linear_smooth = None

        self.beam_size = 1
        self.rotary_emb_dims = 0
        self.mask_broadcast_num_heads = True
        self.compute_bias = True
        self.use_neox_rotary_style = False

        self.out_linear_in_scale = 1.5
        self.quant_round_type = 1
        self.quant_max_bound = 126
        self.quant_min_bound = -126

    def quant_helper(
        self, x, quant_scale, quant_round_type, quant_max_bound, quant_min_bound
    ):
        quant_value = quant_max_bound * quant_scale * x
        if quant_round_type == 0:
            quant_value = paddle.to_tensor(np.rint(quant_value.numpy()))
        else:
            quant_value = paddle.round(quant_value)
        return paddle.cast(
            paddle.clip(quant_value, quant_min_bound, quant_max_bound),
            paddle.int8,
        )

    def mmha_naive(
        self,
        x,
        bias,
        src_mask,
        cache_kv_out,
        qkv_out_scale,
        beam_size,
        mask_broadcast_num_heads,
        compute_bias,
        out_linear_in_scale,
        quant_round_type,
        quant_max_bound,
        quant_min_bound,
    ):
        if qkv_out_scale is not None:
            x = x.cast(cache_kv_out.dtype) * qkv_out_scale + bias
        else:
            x = x + bias

        x = paddle.transpose(
            x, [0, 2, 1, 3]
        )  # [bz, seqlen, nhead, head_dim] --> [bz, nhead, seqlen, head_dim]
        q, k, v = paddle.split(x, 3, axis=2)
        cache_k, cache_v = paddle.split(cache_kv_out, 2, axis=0)
        k = paddle.concat([cache_k.squeeze(0), k], axis=2)
        v = paddle.concat([cache_v.squeeze(0), v], axis=2)

        product = paddle.matmul(
            x=q * (x.shape[3] ** -0.5), y=k, transpose_y=True
        )
        product = product + src_mask
        product = paddle.nn.functional.softmax(product)
        out = paddle.matmul(product, v).transpose([0, 2, 1, 3])

        normalized_out = self.quant_helper(
            out,
            out_linear_in_scale,
            quant_round_type,
            quant_max_bound,
            quant_min_bound,
        )
        return out, normalized_out

    def check_main(
        self,
        x,
        bias,
        src_mask,
        cache_kv_out,
        cache_kv_mmha_out,
        qkv_out_scale,
        out_linear_in_scale,
        dtype,
    ):
        paddle.disable_static()
        if qkv_out_scale is not None:
            x = paddle.to_tensor(x).cast("int32")
            qkv_out_scale = paddle.to_tensor(qkv_out_scale).cast("float32")
        else:
            x = paddle.to_tensor(x).cast(dtype)
        bias = paddle.to_tensor(bias).cast(dtype)
        src_mask = paddle.to_tensor(src_mask).cast(dtype)
        cache_kv_out = paddle.to_tensor(cache_kv_out).cast(dtype)
        cache_kv_mmha_out = paddle.to_tensor(cache_kv_mmha_out).cast(dtype)
        paddle_naive_mmha_out = 0
        paddle_naive_mmha_out = self.mmha_naive(
            x,
            bias,
            src_mask,
            cache_kv_out,
            qkv_out_scale,
            self.beam_size,
            self.mask_broadcast_num_heads,
            self.compute_bias,
            out_linear_in_scale,
            self.quant_round_type,
            self.quant_max_bound,
            self.quant_min_bound,
        )

        paddle_mmha_out = mmha_wrapper(
            x,
            bias,
            src_mask,
            None,
            None,
            None,
            cache_kv_mmha_out,
            qkv_out_scale,
            None,
            None,
            self.beam_size,
            self.rotary_emb_dims,
            self.mask_broadcast_num_heads,
            self.compute_bias,
            self.use_neox_rotary_style,
            out_linear_in_scale,
            self.quant_round_type,
            self.quant_max_bound,
            self.quant_min_bound,
        )
        paddle.enable_static()
        return paddle_naive_mmha_out, paddle_mmha_out

    def test_mmha_fp16(self):
        if not paddle.is_compiled_with_cuda():
            return

        paddle_naive_mmha, paddle_mmha_out = self.check_main(
            self.x,
            self.bias,
            self.src_mask,
            self.cache_kv_out,
            self.cache_kv_mmha_out,
            None,
            -1,
            'bfloat16',
        )
        np.testing.assert_allclose(
            paddle_mmha_out[0].numpy(),
            paddle_naive_mmha[0].numpy(),
            rtol=5e-2,
            atol=5e-2,
        )

    def test_mmha_qkv_out_scale(self):
        if not paddle.is_compiled_with_cuda():
            return

        paddle_naive_mmha, paddle_mmha_out = self.check_main(
            self.x_int,
            self.bias,
            self.src_mask,
            self.cache_kv_out,
            self.cache_kv_mmha_out,
            self.qkv_out_scale,
            -1,
            'float16',
        )
        np.testing.assert_allclose(
            paddle_mmha_out[0].numpy(),
            paddle_naive_mmha[0].numpy(),
            rtol=5e-2,
            atol=5e-2,
        )

    def test_mmha_outlinear_in_scale(self):
        if not paddle.is_compiled_with_cuda():
            return

        paddle_naive_mmha, paddle_mmha_out = self.check_main(
            self.x,
            self.bias,
            self.src_mask,
            self.cache_kv_out,
            self.cache_kv_mmha_out,
            None,
            self.out_linear_in_scale,
            'float16',
        )
        np.testing.assert_allclose(
            paddle_mmha_out[0].numpy(),
            paddle_naive_mmha[1].numpy(),
            rtol=5e-2,
            atol=5e-2,
        )


if __name__ == '__main__':
    unittest.main()
