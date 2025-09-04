import asyncio
import inspect
from typing import Dict, Optional

from src.models.llm.llm_torch import LlmTorch
from src.models.llm.llm_vllm import LllmVllm
from src.shared.logger import CustomLogger
from .settings import Settings

class LLMService:
    def __init__(
        self,
        model_name: str,
        max_concurrency: int,
        request_timeout: float,
        params: Dict,
        system_prompt: str,
        batch_window_ms: int,
        logger: CustomLogger,
        settings: Settings,
    ) -> None:
        self.model_name = model_name
        self._model = None
        self._max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._request_timeout = request_timeout
        self._params = params
        self._system_prompt = system_prompt or ""
        self._batch_window_ms = max(0, int(batch_window_ms))
        self._logger = logger
        self._settings = settings
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        
        if self._settings.MODE == "torch":
            self._model = LlmTorch(
                model_name=self.model_name,
                device=self._settings.DEVICE,
                params=self._params,
                system_prompt=self._system_prompt,
                history_max_tokens=self._settings.HISTORY_MAX_TOKENS,

            )
        else:
            self._model = LllmVllm(
                model_name=self.model_name,
                device=self._settings.DEVICE,
                params=self._params,
                system_prompt=self._system_prompt,
                history_max_tokens=self._settings.HISTORY_MAX_TOKENS,
            )
        
        self._logger.info(f"LLM mode: {self._settings.MODE}")
        self._model.start()
        self._started = True
        self._logger.info("LLMService started")

    async def close(self) -> None:
        if not self._started:
            return
        
        close_fn = getattr(self._model, "close", None)
        if close_fn:
            if inspect.iscoroutinefunction(close_fn):
                await close_fn()
            else:
                await asyncio.to_thread(close_fn)
        
        self._started = False
        self._logger.info("LLMService stopped")

    async def generate(
        self, 
        query: str, 
        context: Optional[str] = None
    ) -> str:
        if not self._started:
            await self.start()

        if self._batch_window_ms > 0:
            await asyncio.sleep(self._batch_window_ms / 1000.0)

        async with self._semaphore:
            try:
                gen_fn = getattr(self._model, "generate")
                
                if inspect.iscoroutinefunction(gen_fn):
                    coro = gen_fn(query, context)
                    if self._request_timeout is not None:
                        return await asyncio.wait_for(coro, timeout=self._request_timeout)
                    return await coro
                else:
                    if self._request_timeout is not None:
                        return await asyncio.wait_for(
                            asyncio.to_thread(gen_fn, query, context),
                            timeout=self._request_timeout
                        )
                    return await asyncio.to_thread(gen_fn, query, context)
                    
            except asyncio.TimeoutError:
                self._logger.error("Generation timeout exceeded")
                raise
            except Exception as e:
                self._logger.error(f"Generation error: {str(e)}")
                raise