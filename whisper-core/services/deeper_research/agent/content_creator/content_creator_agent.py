import os
from typing import  Dict, List, Union

from services.llm.agent.base_agent import BaseAgent


class ContentCreatorAgent(BaseAgent):
    def V__init__(self):
        super().__init__(model_name="Gemini/gemini-2.5-pro")

    PROMPT_TEMPLATE = open("services/deeper_research/agent/content_creator/content_creator.md", "r", encoding="utf-8").read()


    async def parse_response(self, response: str) -> Union[dict, list, str, int, float, bool, None]:

        # 把response 写入文件 public/output/event_article/{time}.md
        # if not os.path.exists("public/output/event_article"):
        #     os.makedirs("public/output/event_article")
        # file_path = os.path.join("public/output/event_article", f"{self.context['topic']}.md")
        # with open(file_path, "w", encoding="utf-8") as f:
        #     f.write(response)

        return response


    async def build_messages(self) -> List[Dict[str, str]]:
        file_path = os.path.join("services/llm/article_agent/style/bi_sytle2.md")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                style_guide = f.read()

        if self.context["article_question_chain"] == "":
            PROMPT_TEMPLATE = open("services/deeper_research/agent/content_creator/content_creator_V2.md", "r", encoding="utf-8").read()
            self.PROMPT_TEMPLATE = PROMPT_TEMPLATE

        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            topic_framework_with_search_results=self.context["article_question_chain"],
            style_guide = style_guide
            )
        return [{'role': 'user', 'content': prompt}]

