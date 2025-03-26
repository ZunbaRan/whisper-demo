def start_deep_research():
    import uvicorn
    uvicorn.run("deep_research_app.api.app:app", host="0.0.0.0", port=8001) 