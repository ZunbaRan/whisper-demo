"""深度研究服务实现"""

import json
from typing import Dict, List, AsyncIterable, Optional, Any, Union
from datetime import datetime
import time

from jinja2 import Template
from pydantic import BaseModel, Field

from services.llm.manager.llm_service_manager import llm_service_manager
from .prompt import DEFAULT_PLANNING_PROMPT, DEFAULT_SUMMARY_PROMPT
from .search_engine import SearchEngine, SearchResult
from .volc_bot import VolcBotSearchEngine
from .models import Message, ChatRequest, ChatResponse


class ResultsSummary(BaseModel):
    """搜索结果汇总
    
    key: 查询关键词
    values: 该查询的搜索结果列表
    """
    ref_dict: Dict[str, List[SearchResult]] = Field(default_factory=dict)

    def add_result(self, query: str, results: List[SearchResult]) -> None:
        """添加搜索结果
        
        Args:
            query: 查询关键词
            results: 搜索结果列表
        """
        if query not in self.ref_dict:
            self.ref_dict[query] = results.copy()
        else:
            extended_references = self.ref_dict.get(query, [])
            extended_references.extend(results)
            self.ref_dict[query] = extended_references

    def to_plaintext(self) -> str:
        """转换为纯文本格式
        
        Returns:
            str: 格式化的文本内容
        """
        output = ""
        for key, value in self.ref_dict.items():
            output += f"\n【查询 \"{key}\" 得到的相关资料】\n"
            output += "\n".join([v.summary_content for v in value])
        return output


class ExtraConfig(BaseModel):
    """额外配置"""
    max_planning_rounds: int = 5
    max_search_words: int = 5
    planning_template: Optional[Any] = DEFAULT_PLANNING_PROMPT
    summary_template: Optional[Any] = DEFAULT_SUMMARY_PROMPT

    class Config:
        """配置类"""
        arbitrary_types_allowed = True


class DeepResearch(BaseModel):
    """深度研究类"""
    # 基础配置
    planning_model: str = Field(default="Volcengine/DeepSeek-R1")
    summary_model: str = Field(default="Volcengine/doubao-pro-1.5")
    search_engine: SearchEngine = Field(default_factory=VolcBotSearchEngine)
    extra_config: ExtraConfig = Field(default_factory=ExtraConfig)

    class Config:
        """配置类"""
        arbitrary_types_allowed = True

    def _create_openai_response(
            self,
            content: str = "",
            reasoning_content: str = "",
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建 OpenAI 格式的响应"""
        response = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self.summary_model,
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": content,
                        "reasoning_content": reasoning_content
                    }
                }
            ]
        }

        if metadata:
            # 处理 metadata 中的 SearchResult 对象
            processed_metadata = {}
            for key, value in metadata.items():
                if key == 'search_results' and isinstance(value, list):
                    # 将 SearchResult 对象转换为字典
                    processed_metadata[key] = [
                        {
                            'query': result.query,
                            'summary_content': result.summary_content,
                            'search_references': [
                                {
                                    'url': ref.url,
                                    'content': ref.content,
                                    'site': ref.site,
                                    'title': ref.title
                                } for ref in result.search_references
                            ] if result.search_references else []
                        } for result in value
                    ]
                else:
                    processed_metadata[key] = value
            response["metadata"] = processed_metadata

        return f"data: {json.dumps(response, ensure_ascii=False)}\n\n"

    async def arun_deep_research(self, request: ChatRequest, question: str) -> ChatResponse:
        """运行深度研究（非流式）

        Args:
            request: 聊天请求
            question: 研究问题

        Returns:
            ChatResponse: 研究结果响应
        """
        references = ResultsSummary()
        buffered_reasoning_content = ""

        # 1. 运行推理
        reasoning_stream = self.astream_planning(
            request=request,
            question=question,
            references=references,
        )

        async for chunk in reasoning_stream:
            if isinstance(chunk, bytes):
                chunk_str = chunk.decode('utf-8')
                if chunk_str.startswith('data: '):
                    try:
                        data = json.loads(chunk_str[6:])
                        if 'choices' in data and data['choices'][0]['delta'].get('reasoning_content'):
                            buffered_reasoning_content += data['choices'][0]['delta']['reasoning_content']
                    except json.JSONDecodeError:
                        continue

        # 2. 运行总结
        request.messages.append(
            Message(
                role="assistant",
                content=buffered_reasoning_content,
            )
        )

        client, _ = llm_service_manager.get_client(self.summary_model)
        messages = [msg.dict() for msg in request.messages]

        if self.extra_config.summary_template:
            system_message = Message(
                role="system",
                content=self.extra_config.summary_template.render(
                    reference=references.to_plaintext(),
                    question=question,
                    meta_info=f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            )
            messages.insert(0, system_message.dict())

        response = await client.chat(messages=messages, model=self.summary_model)
        return ChatResponse(
            id=f"deep_research_{int(time.time())}",
            created=int(time.time()),
            model=self.summary_model,
            choices=[{
                "message": {
                    "role": "assistant",
                    "content": response["choices"][0]["message"]["content"],
                    "reasoning_content": buffered_reasoning_content
                }
            }]
        )

    async def astream_deep_research(self, request: ChatRequest, question: str) \
            -> AsyncIterable[bytes]:
        """流式运行深度研究

        Args:
            request: 聊天请求
            question: 研究问题

        Yields:
            bytes: OpenAI 格式的响应数据流
        """
        references = ResultsSummary()
        buffered_reasoning_content = ""

        # 1. 流式推理
        async for chunk in self.astream_planning(request, question, references):
            buffered_reasoning_content += chunk.decode('utf-8')
            yield chunk

        # 2. 流式总结
        request.messages.append(
            Message(
                role="assistant",
                content=buffered_reasoning_content,
            )
        )

        client, config = llm_service_manager.get_client(self.summary_model)
        messages = [msg.dict() for msg in request.messages]

        if self.extra_config.summary_template:
            system_message = Message(
                role="system",
                content=self.extra_config.summary_template.render(
                    reference=references.to_plaintext(),
                    question=question,
                    meta_info=f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            )
            messages.insert(0, system_message.dict())

        async for content_type, content in client.stream_chat(messages=messages, model=config.model_id):
            response = self._create_openai_response(
                content="" if content_type == "reasoning" else content,
                reasoning_content=content if content_type == "reasoning" else ""
            )
            yield response.encode('utf-8')

        yield b'data: [DONE]\n\n'

    async def astream_planning(
            self,
            request: ChatRequest,
            question: str,
            references: ResultsSummary
    ) -> AsyncIterable[bytes]:
        """流式规划搜索策略

        Args:
            request: 聊天请求
            question: 研究问题
            references: 已有的搜索结果

        Yields:
            bytes: OpenAI 格式的响应数据流
        """
        planned_rounds = 1
        while planned_rounds <= self.extra_config.max_planning_rounds:
            planned_rounds += 1

            client, config = llm_service_manager.get_client(self.planning_model)
            planning_result = ""

            # 构建消息
            messages = [msg.dict() for msg in request.messages]
            if self.extra_config.planning_template:
                system_message = Message(
                    role="system",
                    content=self.extra_config.planning_template.render(
                        reference=references.to_plaintext(),
                        question=question,
                        max_search_words=self.extra_config.max_search_words,
                        meta_info=f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                )
                messages.insert(0, system_message.dict())

            # 获取流式响应
            async for content_type, content in client.stream_chat(messages=messages, model=config.model_id):
                if content_type == "reasoning":
                    response = self._create_openai_response(reasoning_content=content)
                    yield response.encode('utf-8')
                else:
                    planning_result += content
                    response = self._create_openai_response(content=content)
                    yield response.encode('utf-8')

            # 检查是否需要继续搜索
            new_queries = self.check_query(planning_result)
            if not new_queries:
                # 生成完成状态元数据
                response = self._create_openai_response(metadata={'search_state': 'searched'})
                yield response.encode('utf-8')
                break
            else:
                # 生成搜索状态元数据
                response = self._create_openai_response(metadata={
                    'search_rounds': planned_rounds,
                    'search_state': 'searching',
                    'search_keywords': new_queries
                })
                yield response.encode('utf-8')

                # 执行搜索
                search_results = await self.search_engine.asearch(new_queries)

                # 生成搜索完成状态元数据
                response = self._create_openai_response(metadata={
                    'search_rounds': planned_rounds,
                    'search_state': 'searched',
                    'search_keywords': new_queries,
                    'search_results': search_results
                })
                yield response.encode('utf-8')

                # 保存搜索结果
                for search_result in search_results:
                    references.add_result(query=search_result.query, results=[search_result])

        yield b'data: [DONE]\n\n'

    @classmethod
    def check_query(cls, output: str) -> Optional[List[str]]:
        """检查是否需要继续搜索

        Args:
            output: 规划输出内容

        Returns:
            Optional[List[str]]: 需要搜索的关键词列表，None 表示不需要继续搜索
        """
        if '无需' in output:
            return None
        return [o.strip() for o in output.split(';')]
