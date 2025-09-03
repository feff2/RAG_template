import asyncio

from typing import Dict, List

from src.models.llm.llm_torch import LlmTorch
from src.models.llm.llm_vllm import LllmVllm
from src.shared.logger import CustomLogger


class LLMService:
    def __init__(
        self,
        model_name: str,
        max_concurrency: int,
        request_timeout: float,
        params: Dict,
        system_prompt: str,
        client_context: List[str],
        batch_window_ms: int,
        params: Dict,
        wrapper,
    ) -> None:
        self.__wrapper = wrapper
        self.__max_concurrency = max_concurrency
        self.__semaphore = asyncio.Semaphore(max_concurrency)
        self.__request_timeout = request_timeout
        self.__params = params 
        self.__system_prompt = system_prompt or ""
        self.__batch_window_ms = max(0, int(batch_window_ms))
        self.__logger = CustomLogger("Llm_service")

        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        

        self.__logger.info("AsyncLLMService started")

    async def close(self) -> None:
        if not self._started:
            return
        close_fn = getattr(self._wrapper, "close", None)
        if close_fn is not None:
            if inspect.iscoroutinefunction(close_fn):
                await close_fn()  # type: ignore
            else:
                await asyncio.to_thread(close_fn)
        self._started = False
        self.__logger.info("AsyncLLMService stopped")

    # ------------------
    # generate
    # ------------------
    async def generate(self, prompt: str, context: Optional[Union[str, List[str]]] = None, **kwargs) -> str:
        if not self._started:
            await self.start()

        full_prompt = self._build_prompt(prompt, context)
        sampling_params = {**(self._params or {}), **kwargs}

        # cooperative window to increase chance of backend batching
        if self._batch_window_ms > 0:
            await asyncio.sleep(self._batch_window_ms / 1000.0)

        async with self._semaphore:
            gen_fn = getattr(self._wrapper, "generate")
            # generate may be sync or async
            if inspect.iscoroutinefunction(gen_fn):
                coro = gen_fn(full_prompt, **sampling_params)  # type: ignore
                if self._request_timeout is not None:
                    return await asyncio.wait_for(coro, timeout=self._request_timeout)
                return await coro  # type: ignore
            else:
                # blocking -> run in threadpool
                if self._request_timeout is not None:
                    return await asyncio.wait_for(asyncio.to_thread(gen_fn, full_prompt, **sampling_params), timeout=self._request_timeout)
                return await asyncio.to_thread(gen_fn, full_prompt, **sampling_params)

    async def stream_generate(self, prompt: str, context: Optional[Union[str, List[str]]] = None, **kwargs) -> AsyncGenerator[str, None]:
        if not self._started:
            await self.start()

        full_prompt = self._build_prompt(prompt, context)
        sampling_params = {**(self._params or {}), **kwargs}

        if self._batch_window_ms > 0:
            await asyncio.sleep(self._batch_window_ms / 1000.0)

        async def _inner() -> AsyncGenerator[str, None]:
            async with self._semaphore:
                stream_fn = getattr(self._wrapper, "stream_generate", None)

                if stream_fn is None:
                    # Fallback to non-streaming generate
                    result = await self.generate(prompt, context, **kwargs)
                    yield result
                    return

                # If wrapper's stream_generate is async generator
                if inspect.iscoroutinefunction(stream_fn):
                    agen = stream_fn(full_prompt, **sampling_params)  # type: ignore
                    async for piece in agen:  # type: ignore
                        yield str(piece)
                    return

                # If wrapper's stream_generate is sync generator/iterator -> run producer in thread
                q: asyncio.Queue = asyncio.Queue()

                def _producer():
                    try:
                        it = stream_fn(full_prompt, **sampling_params)
                        for piece in it:
                            q.put_nowait(piece)
                    except Exception as e:
                        q.put_nowait(RuntimeError(str(e)))
                    finally:
                        q.put_nowait(None)

                prod_task = asyncio.create_task(asyncio.to_thread(_producer))
                try:
                    while True:
                        item = await q.get()
                        if item is None:
                            break
                        if isinstance(item, Exception):
                            raise item
                        yield str(item)
                finally:
                    prod_task.cancel()

        return _inner()


# ------------------
# Example usage
# ------------------
if __name__ == "__main__":
    # example: how a torch-wrapper or vllm-wrapper should look like
    class DummySyncWrapper:
        def start(self):
            print("start")

        def close(self):
            print("close")

        def generate(self, prompt: str, **kwargs) -> str:
            return prompt + " -- done"

        def stream_generate(self, prompt: str, **kwargs):
            for i in range(3):
                yield f"{prompt} part {i}\n"

    async def demo():
        wrapper = DummySyncWrapper()
        service = AsyncLLMService(wrapper, max_concurrency=2, batch_window_ms=5, system_prompt="[SYS]")
        await service.start()
        print(await service.generate("Hello"))
        async for chunk in service.stream_generate("Hello stream"):
            print(chunk, end="")
        await service.close()

    asyncio.run(demo())
