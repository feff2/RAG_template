"""
Common Validation Logic for Microservices

Eliminates duplicate validation patterns across services.
"""

import re
from typing import Dict, Any, List, Optional, Callable
from fastapi import HTTPException, status


class CommonValidator:
    """Common validation patterns for microservices"""

    # Common regex patterns
    PATTERNS = {
        "text_content": re.compile(
            r"^[\w\s\.,!?;:\'\"()\[\]{}@#$%^&*+=<>/\\|~`\-_]+$", re.UNICODE
        ),
        "doc_id": re.compile(r"^[a-zA-Z0-9_\-\.]+$"),
        "url": re.compile(r"^https?://[^\s/$.?#].[^\s]*$"),
        "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
        "date": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    }

    # Common validation rules
    RULES = {
        "max_text_length": 10000,
        "max_documents_per_request": 1000,
        "max_embedding_dim": 2048,
        "max_prompt_length": 8000,
        "max_history_messages": 50,
        "max_generation_tokens": 2048,
    }

    @classmethod
    def validate_text(
        cls, text: str, field_name: str = "text", max_length: Optional[int] = None
    ) -> List[str]:
        """Validate text content"""
        errors = []

        if not isinstance(text, str):
            errors.append(f"{field_name} must be a string")
            return errors

        max_len = max_length or cls.RULES["max_text_length"]
        if len(text) > max_len:
            errors.append(f"{field_name} too long: {len(text)} > {max_len}")

        if not cls._is_valid_text_content(text):
            errors.append(f"{field_name} contains invalid characters")

        return errors

    @classmethod
    def validate_texts(
        cls, texts: List[str], max_length: Optional[int] = None
    ) -> List[str]:
        """Validate a list of text strings"""
        errors = []

        if not isinstance(texts, list):
            errors.append("texts must be a list")
            return errors

        if len(texts) > cls.RULES["max_documents_per_request"]:
            errors.append(
                f"Too many texts: {len(texts)} > {cls.RULES['max_documents_per_request']}"
            )

        for i, text in enumerate(texts):
            text_errors = cls.validate_text(text, f"texts[{i}]", max_length)
            errors.extend(text_errors)

        return errors

    @classmethod
    def validate_embeddings(
        cls, embeddings: List[List[float]], max_dim: Optional[int] = None
    ) -> List[str]:
        """Validate embedding vectors"""
        errors = []

        if not isinstance(embeddings, list):
            errors.append("embeddings must be a list")
            return errors

        max_dim = max_dim or cls.RULES["max_embedding_dim"]

        for i, emb in enumerate(embeddings):
            if not isinstance(emb, list):
                errors.append(f"embeddings[{i}] must be a list")
                continue

            if len(emb) > max_dim:
                errors.append(
                    f"embeddings[{i}] dimension too large: {len(emb)} > {max_dim}"
                )

            for j, val in enumerate(emb):
                if not isinstance(val, (int, float)):
                    errors.append(f"embeddings[{i}][{j}] must be a number")
                elif not (-100 <= val <= 100):
                    errors.append(f"embeddings[{i}][{j}] value out of range: {val}")

        return errors

    @classmethod
    def validate_metadata(
        cls, metadatas: List[Dict[str, Any]], allowed_keys: Optional[List[str]] = None
    ) -> List[str]:
        """Validate metadata dictionaries"""
        errors = []

        if not isinstance(metadatas, list):
            errors.append("metadatas must be a list")
            return errors

        allowed_keys = allowed_keys or [
            "source",
            "category",
            "author",
            "date",
            "url",
            "title",
        ]

        for i, meta in enumerate(metadatas):
            if not isinstance(meta, dict):
                errors.append(f"metadatas[{i}] must be a dictionary")
                continue

            for key, value in meta.items():
                if allowed_keys and key not in allowed_keys:
                    errors.append(f"metadatas[{i}] contains disallowed key: {key}")

                # Validate specific metadata types
                if key == "url" and not cls._is_valid_url(value):
                    errors.append(f"metadatas[{i}].url is not a valid URL")
                elif key == "email" and not cls._is_valid_email(value):
                    errors.append(f"metadatas[{i}].email is not a valid email")
                elif key == "date" and not cls._is_valid_date(value):
                    errors.append(
                        f"metadatas[{i}].date is not a valid date (YYYY-MM-DD)"
                    )

        return errors

    @classmethod
    def validate_generation_params(cls, params: Dict[str, Any]) -> List[str]:
        """Validate LLM generation parameters"""
        errors = []

        if "max_new_tokens" in params:
            tokens = params["max_new_tokens"]
            if (
                not isinstance(tokens, int)
                or tokens < 1
                or tokens > cls.RULES["max_generation_tokens"]
            ):
                errors.append(
                    f"max_new_tokens must be an integer between 1 and {cls.RULES['max_generation_tokens']}"
                )

        if "temperature" in params:
            temp = params["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                errors.append("temperature must be a number between 0 and 2")

        if "top_p" in params:
            top_p = params["top_p"]
            if not isinstance(top_p, (int, float)) or top_p < 0 or top_p > 1:
                errors.append("top_p must be a number between 0 and 1")

        if "top_k" in params:
            top_k = params["top_k"]
            if not isinstance(top_k, int) or top_k < 1 or top_k > 1000:
                errors.append("top_k must be an integer between 1 and 1000")

        return errors

    @classmethod
    def validate_required_fields(
        cls, data: Dict[str, Any], required_fields: List[str]
    ) -> List[str]:
        """Validate required fields are present"""
        errors = []

        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")

        return errors

    @classmethod
    def _is_valid_text_content(cls, text: str) -> bool:
        """Check if text contains only valid characters"""
        return bool(cls.PATTERNS["text_content"].match(text))

    @classmethod
    def _is_valid_url(cls, url: str) -> bool:
        """Check if string is a valid URL"""
        return bool(cls.PATTERNS["url"].match(url))

    @classmethod
    def _is_valid_email(cls, email: str) -> bool:
        """Check if string is a valid email"""
        return bool(cls.PATTERNS["email"].match(email))

    @classmethod
    def _is_valid_date(cls, date: str) -> bool:
        """Check if string is a valid date in YYYY-MM-DD format"""
        return bool(cls.PATTERNS["date"].match(date))


def validate_and_raise(data: Dict[str, Any], validations: List[Callable], **kwargs):
    """Run validations and raise HTTPException if any fail"""
    errors = []

    for validation in validations:
        if callable(validation):
            validation_errors = validation(data, **kwargs)
            if isinstance(validation_errors, list):
                errors.extend(validation_errors)
            else:
                errors.append(str(validation_errors))

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"validation_errors": errors},
        )

    return data


# Common validation functions for specific use cases
def validate_document_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate document-related requests"""
    validations = [
        lambda d: CommonValidator.validate_required_fields(d, ["texts", "doc_ids"]),
        lambda d: CommonValidator.validate_texts(d.get("texts", [])),
        lambda d: CommonValidator.validate_metadata(d.get("metadatas", []))
        if "metadatas" in d
        else [],
        lambda d: CommonValidator.validate_embeddings(d.get("embeddings", []))
        if "embeddings" in d
        else [],
    ]

    return validate_and_raise(data, validations)


def validate_search_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate search requests"""
    validations = [
        lambda d: CommonValidator.validate_required_fields(d, ["query"]),
        lambda d: CommonValidator.validate_text(d.get("query", ""), "query", 5000),
    ]

    return validate_and_raise(data, validations)


def validate_llm_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate LLM generation requests"""
    validations = [
        lambda d: CommonValidator.validate_required_fields(d, ["prompt"]),
        lambda d: CommonValidator.validate_text(
            d.get("prompt", ""), "prompt", CommonValidator.RULES["max_prompt_length"]
        ),
        lambda d: CommonValidator.validate_generation_params(d),
    ]

    return validate_and_raise(data, validations)
