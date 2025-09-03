import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.services.llm_service import LLMService
from ..settings import Settings

@pytest.fixture
def mock_settings():
    settings = Mock(spec=Settings)
    settings.MODE = "vllm"  
    settings.DEVICE = "cuda"
    settings.HISTORY_MAX_TOKENS = 100
    return settings

@pytest.fixture
def mock_llm_vllm():
    with patch('src.services.llm_service.LlmVllm') as mock:
        instance = mock.return_value
        instance.start = Mock()
        instance.close = Mock()
        instance.generate = AsyncMock(return_value="Test response")
        yield mock

@pytest.mark.asyncio
async def test_llm_service_initialization(mock_settings):
    """Тест инициализации сервиса"""
    service = LLMService(
        model_name="test-model",
        max_concurrency=5,
        request_timeout=30.0,
        params={"temperature": 0.7},
        system_prompt="Test system prompt",
        batch_window_ms=50,
        settings=mock_settings
    )
    
    assert service._started == False
    assert service.model_name == "test-model"
    assert service._max_concurrency == 5
    assert service._system_prompt == "Test system prompt"

@pytest.mark.asyncio
async def test_llm_service_start_and_generate(mock_settings, mock_llm_vllm):
    """Тест запуска сервиса и генерации текста"""
    service = LLMService(
        model_name="test-model",
        max_concurrency=5,
        request_timeout=30.0,
        params={"temperature": 0.7},
        system_prompt="Test system prompt",
        batch_window_ms=50,
        settings=mock_settings
    )
    
    service.start()
    
    assert service._started == True
    
    mock_llm_vllm.assert_called_once_with(
        model_name="test-model",
        device="cpu",
        params={"temperature": 0.7},
        system_prompt="Test system prompt",
        history_max_tokens=100
    )
    
    service._model.start.assert_called_once()
    
    result = await service.generate("Test query", "Test context")
    
    service._model.generate.assert_called_once_with("Test query", "Test context")
    
    assert result == "Test response"

@pytest.mark.asyncio
async def test_llm_service_close(mock_settings):
    """Тест закрытия сервиса"""
    service = LLMService(
        model_name="test-model",
        max_concurrency=5,
        request_timeout=30.0,
        params={"temperature": 0.7},
        system_prompt="Test system prompt",
        batch_window_ms=50,
        settings=mock_settings
    )
    
    service.start()
    assert service._started == True
    
    await service.close()
    
    assert service._started == False
    
    service._model.close.assert_called_once()

@pytest.mark.asyncio
async def test_llm_service_generate_without_start(mock_settings):
    service = LLMService(
        model_name="test-model",
        max_concurrency=5,
        request_timeout=30.0,
        params={"temperature": 0.7},
        system_prompt="Test system prompt",
        batch_window_ms=50,
        settings=mock_settings
    )
    
    assert service._started == False
    
    result = await service.generate("Test query")
    
    assert service._started == True
    
    assert result == "Test response"

@pytest.mark.asyncio
async def test_llm_service_timeout(mock_settings):
    """Тест таймаута при генерации"""
    service = LLMService(
        model_name="test-model",
        max_concurrency=5,
        request_timeout=0.001,  
        params={"temperature": 0.7},
        system_prompt="Test system prompt",
        batch_window_ms=50,
        settings=mock_settings
    )
    
    async def long_generate(*args, **kwargs):
        await asyncio.sleep(1)  # Дольше таймаута
        return "Long response"
    
    service._model.generate = long_generate
    service.start()
    
    with pytest.raises(asyncio.TimeoutError):
        await service.generate("Test query")