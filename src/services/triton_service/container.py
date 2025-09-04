from .triton_client import TritonClient
from .triton_server import TritonServer
from .settings import settings
from src.shared.logger import CustomLogger

from src.models.dense_retriever.bi_enocer_torch import BiEncoderTorch
from src.models.dense_retriever.bi_enocer_onnx import BiEncoderOnnx
from src.models.cross_encoder.cross_encoder_torch import CrossEncoderTorch
from src.models.cross_encoder.cross_encoder_onnx import CrossEncoderOnnx

logger = CustomLogger("triton_service") 


if settings.CROSS_ENCODER_FORMAT == "torch":
    cross_encoder = CrossEncoderTorch(
        model_name=settings.CROSS_ENCODER_PATH,
        device=settings.DEVICE,
    )
else:
    cross_encoder = CrossEncoderOnnx(
        model_name=settings.CROSS_ENCODER_PATH,
        device=settings.DEVICE,
    )

if settings.BI_ENCODER_FORMAT == "torch":
    bi_encoder = BiEncoderTorch(
        model_name=settings.BI_ENCODER_PATH,
        device=settings.DEVICE,
    )
else:
    bi_encoder = BiEncoderOnnx(
        model_name=settings.BI_ENCODER_PATH,
        device=settings.DEVICE,
    )

client = TritonClient(
    inference_host=settings.INFERENCE_HOST,
    bi_encoder_port=settings.BI_ENCODER_PORT,
    cross_encoder_port=settings.CROSS_ENCODER_PORT,
    inference_timeout_s=settings.INFERENCE_TIMEOUT_S,
    bi_encoder_name=settings.BI_ENCODER_NAME,
    cross_encoder_name=settings.CROSS_ENCODER_NAME,
    device=settings.DEVICE,
    logger=logger,
)

server = TritonServer(
    bi_encoder=bi_encoder,
    cross_encoder=cross_encoder,
    logger=logger
)