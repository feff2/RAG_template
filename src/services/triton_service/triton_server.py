import numpy as np
from pytriton.decorators import batch
from pytriton.model_config import DynamicBatcher, ModelConfig, Tensor
from pytriton.triton import Triton, TritonConfig
from src.models.dense_retriever.bi_encoder import BiEncoder
from src.models.cross_encoder.cross_encoder import CrossEncoder
from .settings import settings
from src.shared.logger import CustomLogger

class TritonServer:
    def __init__(self, bi_encoder: BiEncoder, cross_encoder: CrossEncoder, logger: CustomLogger):
        self.triton_config = TritonConfig(metrics_config=["summary_latencies=true"])
        self.bi_encoder = bi_encoder 
        self.cross_encoder = cross_encoder
        self.logger = logger

    @batch
    def _biecoder_infer_fn(self, text: np.ndarray) -> dict[str, np.ndarray]:
        sequence = [np.char.decode(c.astype("bytes"), "utf-8").item() for c in text]
        embedding = self.inference_service.bi_encoder.encode(sequence)
        return {"embeding": embedding}
    
    @batch
    def _cross_encoder_infer_fn(self, pairs: np.ndarray) -> dict[str, np.ndarray]:
        scores = []
        for pair in pairs:
            decoded_pair = []
            for c in pair[0]:
                decoded_text = np.char.decode(c.astype("bytes"), "utf-8").item()
                decoded_pair.append(decoded_text)
            
            for c in pair[1]:
                decoded_text = np.char.decode(c.astype("bytes"), "utf-8").item()
                decoded_pair.append(decoded_text)
            
            score = self.inference_service.cross_encoder.rerank(decoded_pair)
            scores.append(score)
        
        return {"scores": np.array(scores, dtype=np.float16)}
    
    def setup_bi_encoder(self, triton):
        self.logger.info(
            f"Start triton inference MAX_BATCH_SIZE={settings.MAX_BATCH_SIZE}, "
            f"MAX_QUEUE_DELAY_MICROSECONDS={settings.MAX_QUEUE_DELAY_MICROSECONDS}"
        )
        
        triton.bind(
            model_name=settings.BI_ENCODER_NAME,
            infer_func=self._biecoder_infer_fn,
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
    
    def setup_cross_encoder(self, triton):
        self.logger.info(
            f"Start triton inference MAX_BATCH_SIZE={settings.MAX_BATCH_SIZE}, "
            f"MAX_QUEUE_DELAY_MICROSECONDS={settings.MAX_QUEUE_DELAY_MICROSECONDS}"
        )
        
        triton.bind(
            model_name=settings.CROSS_ENCODER_NAME,
            infer_func=self._cross_encoder_infer_fn,
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
    
    def run(self):
        with Triton(config=self.triton_config) as triton:
            self.setup_bi_encoder(triton)
            self.setup_cross_encoder(triton)
            
            self.logger.info("Serving inference")
            self.logger.info(
                f"USE_GPU={settings.USE_GPU}, GPU_INDEX={settings.GPU_INDEX}"
            )
            
            triton.serve()
