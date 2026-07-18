AGENT_TEMPLATES = {
    "planner": {
        "id": "template-planner",
        "name": "Planner Agent",
        "role": "planner",
        "description": "负责将用户 Goal 拆解为可执行的 Task 列表",
        "default_config": {
            "default_model_id": "claude-3-opus",
            "backup_model_ids": ["gpt-4-turbo", "deepseek-chat"],
            "allowed_tools": [],
            "system_prompt": (
                "你是一个任务规划专家。你的职责是将用户的目标拆解为清晰、可执行的任务列表。\n"
                "每个任务必须包含：标题、描述、完成标准、预估复杂度。\n"
                "任务之间如果有依赖关系，请明确指出。"
            ),
            "output_format": "json",
            "max_steps_per_task": 5,
            "allow_handoff": False,
            "handoff_threshold_tokens": 0,
        },
    },
    "coder": {
        "id": "template-coder",
        "name": "Coder Agent",
        "role": "coder",
        "description": "负责编写代码、修改文件、实现功能",
        "default_config": {
            "default_model_id": "deepseek-coder",
            "backup_model_ids": ["claude-3-opus", "gpt-4-turbo"],
            "allowed_tools": ["file_read", "file_write", "terminal_execute"],
            "system_prompt": (
                "你是一个资深开发工程师。你的职责是根据任务描述编写高质量代码。\n"
                "请遵循项目的技术栈和代码规范。\n"
                "如果需要修改现有文件，请先读取文件内容，再生成修改方案。"
            ),
            "output_format": "markdown",
            "max_steps_per_task": 20,
            "allow_handoff": True,
            "handoff_threshold_tokens": 80000,
        },
    },
    "reviewer": {
        "id": "template-reviewer",
        "name": "Reviewer Agent",
        "role": "reviewer",
        "description": "负责审查代码、检查质量、发现 bug",
        "default_config": {
            "default_model_id": "gpt-4-turbo",
            "backup_model_ids": ["claude-3-opus"],
            "allowed_tools": ["workspace_list", "file_read", "file_search", "git_diff", "test_runner", "lint_run", "typecheck_run", "build_run"],
            "system_prompt": (
                "你是一个代码审查专家。你的职责是审查代码修改，检查逻辑正确性、安全性、性能和代码风格。\n"
                "请给出具体的修改建议，指出问题所在行号和原因。"
            ),
            "output_format": "markdown",
            "max_steps_per_task": 10,
            "allow_handoff": True,
            "handoff_threshold_tokens": 60000,
        },
    },
    "research": {
        "id": "template-research",
        "name": "Research Agent",
        "role": "research",
        "description": "负责搜索信息、整理资料、提供技术调研",
        "default_config": {
            "default_model_id": "kimi-long-context",
            "backup_model_ids": ["claude-3-opus", "gpt-4-turbo"],
            "allowed_tools": ["workspace_list", "file_read", "file_search", "glob_search"],
            "system_prompt": (
                "你是一个技术研究员。你的职责是根据任务需求搜索和整理相关信息。\n"
                "请提供来源、关键结论和行动建议。"
            ),
            "output_format": "markdown",
            "max_steps_per_task": 15,
            "allow_handoff": True,
            "handoff_threshold_tokens": 100000,
        },
    },
    "summarizer": {
        "id": "template-summarizer",
        "name": "Summarizer Agent",
        "role": "summarizer",
        "description": "负责压缩上下文、生成交接摘要、总结执行结果",
        "default_config": {
            "default_model_id": "claude-3-haiku",
            "backup_model_ids": ["gpt-3.5-turbo", "deepseek-chat"],
            "allowed_tools": ["workspace_list", "file_read", "file_search"],
            "system_prompt": (
                "你是一个摘要生成专家。你的职责是将复杂的执行过程和上下文压缩为清晰的交接摘要。\n"
                "摘要必须包含：已完成工作、未完成工作、关键约束、已做决策、风险和下一步建议。"
            ),
            "output_format": "json",
            "max_steps_per_task": 3,
            "allow_handoff": False,
            "handoff_threshold_tokens": 0,
        },
    },
    "supervisor": {
        "id": "template-supervisor",
        "name": "Supervisor Agent",
        "role": "supervisor",
        "description": "负责最终审查、判断是否完成任务、生成最终汇总",
        "default_config": {
            "default_model_id": "claude-3-opus",
            "backup_model_ids": ["gpt-4-turbo"],
            "allowed_tools": ["file_read"],
            "system_prompt": (
                "你是一个项目监督者。你的职责是审查所有任务的完成质量，判断 Goal 是否达成。\n"
                "如果存在问题，请指出具体缺陷和改进建议。\n"
                "如果 Goal 达成，请生成结构化的最终汇总报告。"
            ),
            "output_format": "markdown",
            "max_steps_per_task": 5,
            "allow_handoff": False,
            "handoff_threshold_tokens": 0,
        },
    },
}


from typing import Optional, List

def get_template(template_id: str) -> Optional[dict]:
    return AGENT_TEMPLATES.get(template_id)


def list_templates() -> List[dict]:
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "role": t["role"],
            "description": t["description"],
            "default_config": t["default_config"],
        }
        for t in AGENT_TEMPLATES.values()
    ]
