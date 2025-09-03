from dataclasses import dataclass
from typing import Tuple, List

import torch
import numpy as np
from pytriton.client import AsyncioModelClient

from src.models.cross_encoder.cross_encoder_onnx import CrossEncoderOnnx
from src.models.dense_retriever.bi_enocer_onnx import BiEncoderOnnx
from src.models.dense_retriever.bi_enocer_torch import BiEncoderTorch
from src.models.cross_encoder.cross_encoder_torch import CrossEncoderTorch
from src.shared.logger import CustomLogger


@dataclass(frozen=True)
class InferResultBiEncoder:
    result: np.ndarray


@dataclass(frozen=True)
class InferResultCrossEncoder:
    result: np.ndarray


class TritonService:
    def __init__(
        self: "TritonService",
        inference_host: str,
        bi_encoder_port: int,
        cross_encoder_port: int,
        inference_timeout_s: int,
        bi_encoder_name: str,
        cross_encoder_name: str,
        device: torch.device,
    ) -> None:
        self.__inference_host = inference_host
        self.__bi_encoder_port = bi_encoder_port
        self.__cross_encoder_port = cross_encoder_port
        self.__inference_timeout_s = inference_timeout_s
        self.__bi_encoder_name = bi_encoder_name
        self.__cross_encoder_name = cross_encoder_name
        self.__device = device
        self.logger = CustomLogger("triton_client")

    async def encode(
        self: "TritonService",
        text: str,
    ) -> InferResultBiEncoder:
        sequence = np.array([text])
        sequence = np.char.encode(sequence, "utf-8")

        msg = f"Sequence={str(sequence)}"  # noqa: RUF010
        self.logger.debug(msg)

        result_dict = await self.__bi_encoder_client.infer_sample(
            sequence,
        )

        return InferResultBiEncoder(
            result=result_dict["embeding"].tolist(),
        )

    async def rerank(
        self: "TritonService",
        pairs: List[Tuple[str, str]],
    ) -> InferResultCrossEncoder:
        pairs_np = []
        for pair in pairs:
            pairs_np.append((np.array([pair[0]]), np.array([pair[1]])))
            pairs_np[-1] = (
                np.char.encode(pairs_np[-1][0], "utf-8"),
                np.char.encode(pairs_np[-1][1], "utf-8"),
            )

        msg = f"Pair={str(pairs_np)}"  # noqa: RUF010
        self.logger.debug(msg)

        result_dict = await self.__cross_encoder_client.infer_sample(
            pairs_np,
        )

        return InferResultCrossEncoder(
            result=result_dict["score"].tolist(),
        )

    async def destroy(self: "TritonService") -> None:
        await self.__bi_encoder_client.close()
        await self.__cross_encoder_client.close()

    def create_model(self: "TritonService") -> None:
        if self.__settings.bi_encoder_format == "torch":
            self.bi_encoder = BiEncoderTorch(
                model_name=self.__cross_encoder_name,
                device=self.__device,
            )
        else:
            self.bi_encoder = BiEncoderOnnx(
                model_name=self.__cross_encoder_name,
                device=self.__device,
            )

        self.__bi_encoder_client = AsyncioModelClient(
            url=f"{self.__inference_host}:{self.__bi_encoder_port}",
            model_name=self.__bi_encoder_name,
            inference_timeout_s=self.__inference_timeout_s,
        )
        msg = "Bi encoder client started"
        self.logger.info(msg)

        if self.__settings.cross_encoder_format == "torch":
            self.cross_encoder = CrossEncoderTorch(
                model_name=self.__cross_encoder_name,
                device=self.__device,
            )
        else:
            self.cross_encoder = CrossEncoderOnnx(
                model_name=self.__cross_encoder_name,
                device=self.__device,
            )

        self.__cross_encoder_client = AsyncioModelClient(
            url=f"{self.__inference_host}:{self.__cross_encoder_port}",
            model_name=self.__cross_encoder_name,
            inference_timeout_s=self.__inference_timeout_s,
        )
        msg = "Cross encoder client started"
        self.logger.info(msg)
