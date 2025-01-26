from pathlib import Path
from typing import Optional
from pydantic import Field, AliasChoices, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class EnvConfig(BaseSettings):
    # 数据库配置
    debug: bool = Field(
        default=False,
        description="启用调试模式"
    )
    log_level: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )

    chrome_path: str = Field(
        default="",
        description="CHROME 执行路径"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",
        env_nested_delimiter="__",
        extra="ignore",
        validate_default=True,
        protected_namespaces=("model_", "settings_"),
        # secrets_dir="secrets"
    )

# 创建全局配置实例
config = EnvConfig() 