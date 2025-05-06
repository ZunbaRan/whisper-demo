import json
from typing import Union, AsyncGenerator, Tuple, List, Dict, Optional

from services.llm.agent.base_agent import BaseAgent
from services.llm.manager.llm_service_manager import llm_service_manager
from services.llm.search_agent.search_res import SearchRes, References


class ArkWebSearchAgent(BaseAgent):

    def __init__(self):
        super().__init__(model_name="Volcengine/search-bot")
        self.PROMPT_TEMPLATE = None
        self.model_name = "Volcengine/search-bot"
        self.context = {}
        self.result = {}

    async def pre_process(self) -> None:
        pass

    async def build_messages(self) -> List[Dict[str, str]]:
        query = self.context.get("query", "")
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]
        return messages

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[
        Tuple[str, str], None]:
        # 累加 response的结果
        summary_content = ""
        async for role, content in response:
            self.response_stream.append((role, content))  # 保存响应
            summary_content += content
            yield role, content

        self.context["summary_content"] = summary_content

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: str) -> Union[dict, list, str, int, float, bool, None]:
        pass

    async def call(
            self,
            content: Optional[str] = None,
            files: Optional[List[Dict[str, str]]] = None,
            **kwargs
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """Agent的主要调用方法，针对智谱AI的特定实现

        Args:
            content: 主要输入内容
            files: 可选的文件列表，每个文件是一个字典，包含文件路径和内容
            **kwargs: 其他参数

        Yields:
            Tuple[str, str]: (role, content) 元组
        """

        client, model_config = llm_service_manager.get_client(model_name=self.model_name)
        # 获取到的client是ArkClient
        self.context["query"] = content
        messages = await self.build_messages()
        generator, references = await client.stream_bot_chat(messages, model=model_config.model_id)

        # 使用生成器获取流式响应, 并进行收集处理
        async for role, content in self.process_response(generator):
            yield role, content

        # 在生成器运行完毕后，references 列表才会包含所有数据
        if references:
            reference_list = []
            # 打印所有的 references
            for ref in references:
                 reference_list.append(References(
                    site=ref.site_name if hasattr(ref, 'site_name') else "",
                    url=ref.url if hasattr(ref, 'url') else "",
                    content=ref.summary if hasattr(ref, 'summary') else "",
                    title=ref.title if hasattr(ref, 'title') else ""
                ))

            self.context["references"] = reference_list

        search_res = SearchRes(
            query=self.context["query"],
            summary_content=self.context["summary_content"],
            search_references=self.context["references"]
        )

        self.result = search_res
