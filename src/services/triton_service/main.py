import numpy as np
from pytriton.decorators import batch
from pytriton.model_config import DynamicBatcher, ModelConfig, Tensor
from pytriton.triton import Triton, TritonConfig
from .service import TritonService
from .settings import settings


def main() -> None:
    triton_config = TritonConfig(metrics_config=["summary_latencies=true"])

    inference_service = TritonService(
        inference_host=settings.INFERENCE_HOST,
        bi_encoder_port=settings.BI_ENCODER_PORT,
        cross_encoder_port=settings.CROSS_ENCODER_PORT,
        inference_timeout_s=settings.INFERENCE_TIMEOUT_S,
        bi_encoder_name=settings.BI_ENCODER_NAME,
        cross_encoder_name=settings.CROSS_ENCODER_NAME,
        device=settings.DEVICE,
    )

    @batch
    def _biecoder_infer_fn(
        text: np.ndarray,
    ) -> dict[str, np.ndarray]:
        sequence = [np.char.decode(c.astype("bytes"), "utf-8").item() for c in text]
        embedding = inference_service.bi_encoder.encode(sequence)
        return {"embeding": embedding}

    with Triton(config=triton_config) as triton:
        msg = f"Start triton inference MAX_BATCH_SIZE={settings.MAX_BATCH_SIZE}, MAX_QUEUE_DELAY_MICROSECONDS={settings.MAX_QUEUE_DELAY_MICROSECONDS}"
        inference_service.logger.info(msg)

        triton.bind(
            model_name=settings.BI_ENCODER_NAME,
            infer_func=_biecoder_infer_fn,
            inputs=[
                Tensor(name="text", dtype=np.bytes_, shape=(1,)),
            ],
            outputs=[
                Tensor(name="comment", dtype=np.float32, shape=(1,)),
            ],
            config=ModelConfig(
                batching=True,
                max_batch_size=settings.MAX_BATCH_SIZE,
                batcher=DynamicBatcher(
                    preferred_batch_size=[2, 4, 8],
                    max_queue_delay_microseconds=settings.MAX_QUEUE_DELAY_MICROSECONDS,
                ),
            ),
            strict=True,
        )

        inference_service.logger.info("Serving inference")

        msg = f"USE_GPU={settings.USE_GPU}, GPU_INDEX={settings.GPU_INDEX}"
        inference_service.logger.info(msg)

        triton.serve()

    @batch
    def _cross_encoder_infer_fn(
        pairs: np.ndarray,
    ) -> dict[str, np.ndarray]:
        scores = []
        for pair in pairs:
            pair = []
            for c in pair[0]:
                c = np.char.decode(c.astype("bytes"), "utf-8").item()

            for c in pair[1]:
                c = np.char.decode(c.astype("bytes"), "utf-8").item()

            score = inference_service.cross_encoder.rerank(pair)
            scores.append(score)

        return {"scores": scores}

    with Triton(config=triton_config) as triton:
        msg = f"Start triton inference MAX_BATCH_SIZE={settings.MAX_BATCH_SIZE}, MAX_QUEUE_DELAY_MICROSECONDS={settings.MAX_QUEUE_DELAY_MICROSECONDS}"
        inference_service.logger.info(msg)

        triton.bind(
            model_name=settings.CROSS_ENCODER_NAME,
            infer_func=_cross_encoder_infer_fn,
            inputs=[
                Tensor(name="pairs", dtype=np.bytes_, shape=(1,)),
            ],
            outputs=[
                Tensor(name="scores", dtype=np.float16, shape=(1,)),
            ],
            config=ModelConfig(
                batching=True,
                max_batch_size=settings.MAX_BATCH_SIZE,
                batcher=DynamicBatcher(
                    preferred_batch_size=[2, 4, 8],
                    max_queue_delay_microseconds=settings.MAX_QUEUE_DELAY_MICROSECONDS,
                ),
            ),
            strict=True,
        )

        inference_service.logger.info("Serving inference")

        msg = f"USE_GPU={settings.USE_GPU}, GPU_INDEX={settings.GPU_INDEX}"
        inference_service.logger.info(msg)

        triton.serve()


if __name__ == "__main__":
    main()
