"""Search group moderation utilities.

This module encapsulates the message filtering logic we use in the
search群组 to阻止广告/无关内容。设计成独立模块, 方便未来拆分成
独立的“广告管控 Bot”。
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SearchGroupModerator:
    """负责控制搜索群内的消息, 只允许搜索关键词."""

    DEFAULT_ALLOWED_PATTERN = r"^[\u4e00-\u9fa5a-zA-Z0-9#@\s]+$"
    URL_PATTERN = re.compile(r"(https?://|www\.)", re.IGNORECASE)
    DISALLOWED_ENTITY_TYPES = {
        "url",
        "text_link",
        "email",
        "phone_number",
        "mention",
    }

    def __init__(
        self,
        allowed_pattern: str = DEFAULT_ALLOWED_PATTERN,
        max_length: int = 64,
        warning_template: str = "❌ 这里只能输入搜索关键字，请勿发送广告或其它内容。",
        warning_ttl: int = 8,
    ) -> None:
        self.allowed_pattern = re.compile(allowed_pattern)
        self.max_length = max_length
        self.warning_template = warning_template
        self.warning_ttl = warning_ttl

    async def ensure_allowed(self, message, *, is_admin: bool = False) -> bool:
        """返回 True 表示消息允许, False 表示已处理(删除+提醒)."""

        allowed, reason = self._evaluate_message(message, is_admin=is_admin)
        if allowed:
            return True

        await self._handle_violation(message, reason)
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evaluate_message(self, message, *, is_admin: bool) -> Tuple[bool, Optional[str]]:
        """检查消息是否符合规则."""

        if is_admin:
            return True, None

        if not message:
            return False, "系统错误"

        user = getattr(message, "from_user", None)
        if user is not None and user.is_bot:
            return True, None  # 不处理机器人消息

        text = (message.text or "").strip()

        # 只允许纯文本
        has_media = any(
            getattr(message, attr, None)
            for attr in (
                "photo",
                "video",
                "document",
                "animation",
                "voice",
                "audio",
                "sticker",
            )
        )

        if has_media or getattr(message, "caption", None):
            return False, "只允许输入文本关键字"

        if not text:
            return False, "请输入搜索关键字"

        # 长度限制
        if len(text) > self.max_length:
            return False, f"文字长度请控制在 {self.max_length} 字以内"

        # 检查链接/广告
        if self.URL_PATTERN.search(text):
            return False, "请不要发送链接或广告"

        # 检查实体 (链接 / @人 等)
        for entity in message.entities or []:
            if entity.type in self.DISALLOWED_ENTITY_TYPES:
                return False, "请不要发送链接或@他人"

        # 正则匹配合法字符
        if not self.allowed_pattern.fullmatch(text):
            return False, "请仅输入中文/英文/数字等简单关键字"

        return True, None

    async def _handle_violation(self, message, reason: Optional[str]) -> None:
        """删除违规消息并给出提示."""

        try:
            await message.delete()
        except Exception as exc:  # pragma: no cover - Telegram 限制时可能抛错
            logger.warning("删除违规消息失败: %s", exc)

        if not self.warning_template:
            return

        warn_text = self.warning_template
        if reason:
            warn_text = f"{warn_text}\n👉 {reason}"

        try:
            warning_message = await message.chat.send_message(warn_text)
        except Exception as exc:  # pragma: no cover
            logger.warning("发送提醒消息失败: %s", exc)
            return

        if self.warning_ttl:
            asyncio.create_task(self._auto_delete_warning(warning_message))

    async def _auto_delete_warning(self, warning_message) -> None:
        """延迟删除提醒消息, 避免刷屏."""

        try:
            await asyncio.sleep(self.warning_ttl)
            await warning_message.delete()
        except Exception:  # pragma: no cover
            pass


