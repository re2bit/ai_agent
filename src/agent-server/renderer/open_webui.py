import json
from typing import Any, AsyncIterator
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from logging import Logger


class OpenWebUiRenderer:
    logger: Logger

    def __init__(
            self,
            logger: Logger
    ):
        self.logger = logger

    @staticmethod
    def send_message(message: Any) -> str :
        return f"data: {json.dumps(message)}\n"

    async def render(self, event_stream: AsyncIterator[dict[str, Any] | Any]):
        try:
            stream_start_msg = {
                'choices': [
                    {
                        'delta': {},
                        'finish_reason': None
                    }
                ]
            }

            yield self.send_message(stream_start_msg)

            status_message = {
                "event": {
                    "type": "status",
                    "data": {
                        "description": "Datenbank Zugriff gestartet",
                        "done": False,
                    },
                }
            }

            yield self.send_message(status_message)

            async for event in event_stream:
                if "messages" in event:
                    message = event["messages"][-1]
                    if isinstance(message, HumanMessage):
                        continue
#                    if not isinstance(message, AIMessage):
#                        continue
                    if hasattr(message, "content") and message.content:
                        content = message.content

                        if isinstance(message, ToolMessage):
                            if "```" not in content:
                                content = f"\n```\n{content}\n```\n"

                        if (hasattr(message, "tool_calls") and message.tool_calls) or isinstance(message, ToolMessage):
                            content_msg = {
                                'choices':
                                    [
                                        {
                                            'delta':
                                                {
                                                    'reasoning_content': content,
                                                },
                                            'finish_reason': None
                                        }
                                    ]
                            }
                        else:
                            content_msg = {
                                'choices': [
                                    {
                                        'delta': {
                                            'content': content,
                                        },
                                        'finish_reason': None
                                    }
                                ]
                            }

                        yield self.send_message(content_msg)

            status_end_message = {
                "event": {
                    "type": "status",
                    "data": {
                        "description": "Datenbank Zugriff beendet",
                        "done": True
                    },
                }
            }
            yield self.send_message(status_end_message)

            stream_end_msg = {
                'choices': [
                    {
                        'delta': {},
                        'finish_reason': 'stop'
                    }
                ]
            }
            yield self.send_message(stream_end_msg)

        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            error_msg = {
                'error': str(e)
            }
            yield self.send_message(error_msg)