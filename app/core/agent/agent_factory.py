import os
import sys
import yaml
import inspect
import dotenv
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from app.core.memory import CheckpointFactory
from app.core.model.llm_factory import LLMFactory
from app.storage import MongoDBManager

# Tải deepagents. Chú ý chống lỗi nếu thư viện không tồn tại.
try:
    from deepagents import create_deep_agent
except ImportError as e:
    raise ImportError(
        "Could not import 'create_deep_agent' from 'deepagents'. "
        "Please ensure 'deepagents' is installed in the environment."
    ) from e


class AgentFactory:
    """
    AgentFactory quản lý việc tải cấu hình từ các file YAML và khởi tạo các Deep Agent.
    Áp dụng Singleton Pattern để đảm bảo duy nhất một instance quản lý trong suốt vòng đời ứng dụng.
    """
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AgentFactory, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_dir: Optional[str] = None):
        if self._initialized:
            return

        # Đường dẫn mặc định đến thư mục cấu hình app/config
        if config_dir is None:
            # Lấy thư mục gốc của dự án (project root)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Di chuyển lên 2 cấp từ app/core/agent đến app và đi vào config
            self.config_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "config"))
        else:
            self.config_dir = os.path.abspath(config_dir)

        # Tự động thêm deep_research vào sys.path để hỗ trợ import research_agent và các tools của nó
        project_root = os.path.abspath(os.path.join(self.config_dir, "..", ".."))
        deep_research_dir = os.path.join(project_root, "deep_research")
        dotenv.load_dotenv()
        if os.path.exists(deep_research_dir) and deep_research_dir not in sys.path:
            sys.path.append(deep_research_dir)

        self._initialized = True

    def _load_yaml_config(self, agent_name: str) -> dict:
        """
        Tải file cấu hình YAML của agent từ thư mục config.
        Hỗ trợ cả đuôi .yml và .yaml.
        """
        # Loại bỏ đuôi nếu người dùng truyền vào cả đuôi file
        base_name = agent_name
        if base_name.endswith(".yml"):
            base_name = base_name[:-4]
        elif base_name.endswith(".yaml"):
            base_name = base_name[:-5]

        yml_path = os.path.join(self.config_dir, f"{base_name}.yml")
        yaml_path = os.path.join(self.config_dir, f"{base_name}.yaml")

        path_to_load = None
        if os.path.exists(yml_path):
            path_to_load = yml_path
        elif os.path.exists(yaml_path):
            path_to_load = yaml_path
        else:
            raise FileNotFoundError(
                f"Configuration file for agent '{agent_name}' not found in {self.config_dir} "
                f"(tried both .yml and .yaml)"
            )

        try:
            with open(path_to_load, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if not config:
                    raise ValueError(f"Configuration file '{path_to_load}' is empty or invalid")
                return config
        except Exception as e:
            # Chống lỗi: Đảm bảo quăng ngoại lệ chi tiết khi có lỗi cú pháp hoặc file yml hỏng
            raise RuntimeError(f"Error loading YAML configuration from '{path_to_load}': {str(e)}") from e

    def _resolve_system_prompt(self, config: dict, prompt_variables: dict = None) -> str:
        """
        Lấy nội dung system prompt từ config (trực tiếp hoặc đọc từ file)
        và format các biến an toàn.
        """
        system_prompt = config.get("system_prompt", "")
        system_prompt_path = config.get("system_prompt_path", "")

        if system_prompt_path:
            # Nếu đường dẫn tương đối, giải quyết từ gốc dự án hoặc config_dir
            if not os.path.isabs(system_prompt_path):
                # Thử tìm tương đối từ gốc dự án trước
                project_root = os.path.abspath(os.path.join(self.config_dir, "..", ".."))
                full_path = os.path.abspath(os.path.join(project_root, system_prompt_path))
                if not os.path.exists(full_path):
                    # Thử tìm tương đối từ config_dir
                    full_path = os.path.abspath(os.path.join(self.config_dir, system_prompt_path))
            else:
                full_path = system_prompt_path

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    system_prompt = f.read()
            except Exception as e:
                raise RuntimeError(f"Error reading system prompt from file '{full_path}': {str(e)}") from e

        # Format prompt an toàn (tránh KeyError với các dấu ngoặc nhọn JSON/XML)
        if system_prompt and prompt_variables is not None:
            for key, val in prompt_variables.items():
                placeholder = "{" + str(key) + "}"
                if placeholder in system_prompt:
                    system_prompt = system_prompt.replace(placeholder, str(val))

        return system_prompt

    def _resolve_tools(self, tool_names: Optional[List[str]]) -> List[Any]:
        """
        Chuyển đổi danh sách tên tool thành các instance tool thực tế.
        """
        if not tool_names:
            return []

        resolved_tools = []
        for name in tool_names:
            try:
                tool_instance = self._get_tool_by_name(name)
                resolved_tools.append(tool_instance)
            except Exception as e:
                # Chống lỗi: Ghi nhận lỗi chi tiết của từng tool
                raise RuntimeError(f"Failed to resolve tool '{name}': {str(e)}") from e

        return resolved_tools

    def _get_tool_by_name(self, name: str) -> Any:
        """
        Tìm kiếm và khởi tạo tool dựa trên tên trong app.core.tool hoặc deep_research.
        """
        # 1. Thử tìm trong app.core.tool
        try:
            import app.core.tool as app_tools
            tool_attr = getattr(app_tools, name, None)
            if tool_attr is not None:
                if inspect.isclass(tool_attr) and issubclass(tool_attr, BaseTool):
                    return tool_attr()
                return tool_attr
        except ImportError:
            pass

        # 2. Thử tìm trong research_agent.tools (sau khi đã thêm deep_research vào sys.path)
        try:
            import research_agent.tools as dr_tools
            tool_attr = getattr(dr_tools, name, None)
            if tool_attr is not None:
                if inspect.isclass(tool_attr) and issubclass(tool_attr, BaseTool):
                    return tool_attr()
                return tool_attr
        except (ImportError, AttributeError):
            pass

        # 3. Thử tìm dạng package đầy đủ deep_research.research_agent.tools
        try:
            import deep_research.research_agent.tools as dr_tools_legacy
            tool_attr = getattr(dr_tools_legacy, name, None)
            if tool_attr is not None:
                if inspect.isclass(tool_attr) and issubclass(tool_attr, BaseTool):
                    return tool_attr()
                return tool_attr
        except (ImportError, AttributeError):
            pass

        # 4. Hỗ trợ import động thông qua định dạng module_path:attribute_name (ví dụ: app.core.tool.vector_search:VectorSearch)
        if ":" in name:
            try:
                module_path, attr_name = name.split(":")
                import importlib
                module = importlib.import_module(module_path)
                tool_attr = getattr(module, attr_name)
                if inspect.isclass(tool_attr) and issubclass(tool_attr, BaseTool):
                    return tool_attr()
                return tool_attr
            except Exception as e:
                raise ValueError(f"Failed to import tool '{name}' from module: {str(e)}")

        raise ValueError(
            f"Tool '{name}' not found in app.core.tool, research_agent.tools or deep_research.research_agent.tools")

    def _resolve_subagent_config(self, subagent_name: str, prompt_variables: dict = None) -> dict:
        """
        Tải cấu hình subagent từ file YAML và định dạng nó thành dictionary
        phù hợp với yêu cầu của deepagents.
        """
        config = self._load_yaml_config(subagent_name)
        return self._parse_subagent_dict(config, prompt_variables)

    def _parse_subagent_dict(self, config: dict, prompt_variables: dict) -> dict:
        """
        Parse một dictionary cấu hình subagent sang cấu trúc chuẩn của deepagents.
        """
        name = config.get("name")
        description = config.get("description")

        if not name:
            raise ValueError("Subagent configuration must contain a 'name' field")
        if not description:
            raise ValueError(f"Subagent '{name}' configuration must contain a 'description' field")

        system_prompt = self._resolve_system_prompt(config, prompt_variables)
        tools = self._resolve_tools(config.get("tools", []))

        subagent_dict = {
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "tools": tools,
        }

        # Nếu subagent có cấu hình model riêng, ta khởi tạo model cho nó bằng LLMFactory
        # provider = config.get("provider")
        # model_name = config.get("model_name")
        # if provider or model_name:
        #     temperature = config.get("temperature", 0.0)
        #     try:
        #         model = LLMFactory.get_llm(
        #             provider=provider,
        #             model_name=model_name,
        #             temperature=temperature
        #         )
        #         subagent_dict["model"] = model
        #     except Exception as e:
        #         # Chống lỗi: Đảm bảo lỗi LLM của subagent không làm hỏng hoàn toàn ứng dụng nếu có cơ chế fallback
        #         raise RuntimeError(
        #             f"Failed to initialize LLM for subagent '{name}' with provider '{provider}' and model '{model_name}': {str(e)}"
        #         ) from e

        # Nếu subagent có subagents lồng nhau nữa (đệ quy)
        subagents_config = config.get("subagents", [])
        if subagents_config:
            resolved_subagents = []
            for subagent_item in subagents_config:
                if isinstance(subagent_item, str):
                    subagent_data = self._resolve_subagent_config(subagent_item, prompt_variables)
                    resolved_subagents.append(subagent_data)
                elif isinstance(subagent_item, dict):
                    subagent_data = self._parse_subagent_dict(subagent_item, prompt_variables)
                    resolved_subagents.append(subagent_data)
            subagent_dict["subagents"] = resolved_subagents

        return subagent_dict

    def create_agent(self, agent_name: str, **kwargs) -> Any:
        """
        Khởi tạo một deep agent từ file cấu hình YAML.

        Args:
            agent_name: Tên file cấu hình YAML (không cần đuôi .yml).
            **kwargs: Các biến bổ sung dùng để format system prompt.

        Returns:
            Một instance của deep agent được tạo bởi deepagents.create_deep_agent.
        """
        try:
            # 1. Load cấu hình từ YAML
            config = self._load_yaml_config(agent_name)

            # 2. Khởi tạo LLM cho Agent chính thông qua LLMFactory
            provider = config.get("provider") or os.environ.get("DEFAULT_LLM_PROVIDER")
            model_name = config.get("model_name") or os.environ.get("DEFAULT_LLM_MODEL")
            temperature = config.get("temperature", 0.0)

            try:
                model = LLMFactory.get_llm(
                    provider=provider,
                    model_name=model_name,
                    temperature=temperature
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize LLM for orchestrator agent '{agent_name}': {str(e)}"
                ) from e

            # 4. Resolve tools cho Agent chính
            tools = self._resolve_tools(config.get("tools", []))

            # 5. Resolve system prompt
            system_prompt = self._resolve_system_prompt(config, None)

            # 6. Resolve subagents
            subagents_config = config.get("subagents", [])
            resolved_subagents = []

            for subagent_item in subagents_config:
                if isinstance(subagent_item, str):
                    subagent_data = self._resolve_subagent_config(subagent_item, )
                    resolved_subagents.append(subagent_data)
                elif isinstance(subagent_item, dict):
                    subagent_data = self._parse_subagent_dict(subagent_item, )
                    resolved_subagents.append(subagent_data)

            # 7. Khởi tạo deep agent
            try:
                agent = create_deep_agent(
                    model=model,
                    tools=tools,
                    system_prompt=system_prompt,
                    subagents=resolved_subagents,
                    checkpointer=CheckpointFactory.get_checkpoint()
                )
                return agent
            except Exception as e:
                # Chống lỗi khi gọi thư viện bên ngoài deepagents
                raise RuntimeError(f"Error calling create_deep_agent from deepagents: {str(e)}") from e

        except Exception as e:
            # Đảm bảo quăng lỗi chi tiết và ghi nhận nguyên nhân
            raise RuntimeError(f"Failed to create agent '{agent_name}': {str(e)}") from e
