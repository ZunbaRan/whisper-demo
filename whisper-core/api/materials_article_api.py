import logging
from fastapi import APIRouter
from services.deeper_research.create_chain_from_text_flow import CreateChainFromTextFlow

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/create_chain_by_materials")
async def create_chain_by_materials(content: str) -> str:
    workflow = CreateChainFromTextFlow()

    res = ""
    async for result in workflow.astream_execute(content):
        res += result[1]

    # 打印带边框的内容
    border = "-" * 50
    print(f"\n{border}")
    for line in res.split('\n'):
        processed_line = line.strip()
        if processed_line:  # 过滤空行
            print(f"| {processed_line.ljust(48)} |")  # 固定宽度左对齐
    print(f"{border}\n")

    return res




