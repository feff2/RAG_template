@app.post("/process")
async def process_query(request: PipelineRequest):
    try:
        # Получаем историю сессии (если есть)
        session_history = session_cache.get(request.session_id, [])
        
        # 1. Получаем кандидатов через bi-encoder
        retrieval_result = await call_service(
            SERVICES["bi_encoder"],
            {
                "query": request.query,
                "top_k": 100,
                "filters": {}  # Добавьте фильтры при необходимости
            }
        )
        
        # 2. Переранжируем через cross-encoder
        reranking_result = await call_service(
            SERVICES["cross_encoder"],
            {
                "query": request.query,
                "documents": retrieval_result["documents"],
                "top_k": 10
            }
        )
        
        # 3. Формируем контекст с историей
        context = format_context(reranking_result["documents"])
        full_context = add_history_to_context(context, session_history)
        
        # 4. Генерируем ответ через LLM
        llm_response = await call_service(
            SERVICES["llm"],
            {
                "query": request.query,
                "context": full_context,
                "history": session_history,
                "temperature": 0.1
            }
        )
        
        # 5. Обновляем историю сессии
        update_session_history(
            request.session_id, 
            request.query, 
            llm_response["response"]
        )
        
        return {"response": llm_response["response"]}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
