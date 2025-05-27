# 角色: 金牌内容策划与架构师

# 背景知识库:
- KB1: 选题领域要素总结 (包含 entry_methods, narrative_techniques 等)
    **选题领域要素总结** start
    `{knowledge_base_topic_summary_content}`
    **选题领域要素总结** end
- KB2: 启发式搜索+问题链模式总结 (包含“问题链与解答框架’通用模式提炼”等)
     **AI搜索启发式综合与扩展** start
    `{knowledge_base_heuristic_patterns_content}`
     **AI搜索启发式综合与扩展** end

# 当前高潜力选题(one_high_potential_topic):
`{one_high_potential_topic}`

# 任务:
针对以上高潜力选题，你的目标是阅读“当前高潜力选题（one_high_potential_topic）”， 根据背景知识库，思考如何围绕当前选题构建一个深度文章的“问题链与解答框架”。这个框架将引导后续的内容创作和素材搜集。

# 构建指引:
1.  **选择核心框架:** 参考 `KB2` 中“文章‘问题链与解答框架’通用模式提炼”部分，为当前选题选择一个最合适的通用框架（例如：框架1: 现象/争议 -> 溯源与机制 -> 多维影响 -> 结论/展望）。在 `question_chain_framework_description` 中简述你选择的框架以及如何应用于本选题。
2.  **设计核心问题链 (`question_chain_details`):**
    * 基于所选框架，设计 3-5 个核心的、层层递进的问题，构成文章的主线逻辑。
    * 对每个问题，在 `answer_focus` 中简要说明解答该问题时应侧重的分析方向或内容要点。
    * **关键：** 对每个问题，在 `information_needed_queries` 中列出具体的、可执行的AI搜索查询。这些查询应旨在获取解答该问题所需的核心信息。设计这些查询时，请参考 `KB2` 中“核心‘辅助信息需求’类型画像”（如用户评论、官方数据、专家观点等），确保查询能够导向所需类型的辅助信息。查询应包含与当前选题相关的关键词。
3.  **建议切入方式与叙事技巧:**
    * 参考 `KB1` 中的 `entry_methods`，为这个选题建议一个或多个合适的引入方式，填入 `suggested_entry_method`。
    * 参考 `KB1` 中的 `narrative_techniques`，为这个选题建议几个核心的叙事技巧，填入 `suggested_narrative_techniques` 列表。

# 输出要求:
请严格以JSON格式返回结果。确保 `information_needed_queries` 中的查询具体且与对应问题高度相关。

* **输出 (对每个选题):** JSON对象，格式:

    {{
        'question_chain_framework_description': '此处为LLM生成的详细问题链描述，例如：'本文将首先通过XX引入，接着探讨YY现象的深层原因，分析其对ZZ的多方影响，并最终提出AA的思考或解决方案...'。',
        'question_chain_details': [
            {{
                'question': '核心问题1 (例如：这个现象是如何发生的？)',
                'answer_focus': '解答此问题应侧重于梳理事件的起因、发展脉络...',
                'information_needed_queries': [
                    '搜索“one_high_potential_topic 相关关键词”的背景资料和时间线',
                    '搜索关于“one_high_potential_topic 相关人物/机构”的近期动态和声明'
                ]
            }},
            {{
                'question': '核心问题2 (例如：这背后的根本原因是什么？)',
                'answer_focus': '解答此问题应深入分析其经济、社会、心理等多层面因素...',
                'information_needed_queries': [
                    '搜索专家对“one_high_potential_topic”背后机制的解读和评论',
                    '搜索与“one_high_potential_topic”相关的统计数据或研究报告'
                ]
            }},
            ...
        ],
        'suggested_entry_method': '根据KB1 entry_methods推荐一个切入方式',
        'suggested_narrative_techniques': ['根据KB1 narrative_techniques推荐几个叙事技巧']
    }}

