# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# Licensed under the 【火山方舟】原型应用软件自用许可协议
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://www.volcengine.com/docs/82379/1433703
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

"""
for server
    export ARK_API_KEY=877e8151-2569-4337-a3e2-04f6ae9d5157
     export REASONING_MODEL=deepseek-r1-250120
     export SEARCH_ENGINE=volc_bot
     export SEARCH_BOT_ID=bot-20250325153842-sgrjg
"""

# recommend to use DeepSeek-R1 model
# REASONING_MODEL = "ep-20250211101729-97nwq"
REASONING_MODEL = "deepseek-r1-250120"
# default set to volc bot, if using tavily, change it into "tavily"
SEARCH_ENGINE =  "volc_bot"
# optional, if you select tavily as search engine, please configure this
TAVILY_API_KEY = "{YOUR_TAVILY_API_KEY}"
# optional, if you select volc bot as search engine, please configure this
SEARCH_BOT_ID = "bot-20250325153842-sgrjg"

"""
for webui
"""

# ark api key
ARK_API_KEY = "877e8151-2569-4337-a3e2-04f6ae9d5157"
# api server address for web ui
# API_ADDR = "https://ark.cn-beijing.volces.com/api/v3/bots"
API_ADDR = "http://localhost:8888/api/v3/bots"
# while using remote api, need bot id
API_BOT_ID = "bot-20250325153842-sgrjg"
