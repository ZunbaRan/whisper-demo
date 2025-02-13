import uvicorn

# 这个原来是测试的，暂时不用，使用根目录的 run.py
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 