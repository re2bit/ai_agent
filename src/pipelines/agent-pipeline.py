import os
import requests
from pydantic import BaseModel, Field
from typing import List, Union, Generator, Iterator, Optional

class Pipeline:
    class Valves(BaseModel):
        API_URL: str = Field(default="http://agent-server:8000/stream", description="Agent Server")

    def __init__(self):
        self.id = "Retro Nerds - Agent"
        self.name = "Retro Nerds Agent"
        self.version = "0.0.1"
        self.description = (
            "Retro Nerds Agent for Data retrieval bot for Internet Archive."
            ""
            "This Pipeline will call the Internet Archive... yada yada"
        )
        self.author = "René Gerritsen"
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )
        pass

    async def on_startup(self):
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        print(f"inlet: {__name__}")
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        print(f"outlet: {__name__}")
        return body

    def pipe(
            self,
            user_message: str,
            model_id: str,
            messages: List[dict],
            body: dict
    ) -> Union[str, Generator, Iterator]:

        #data = {
        #    "messages": [[msg['role'], msg['content']] for msg in messages],
        #}

        data = {
            "question": messages[-1]['content']
        }

        headers = {
            'accept': 'text/event-stream',
            'Content-Type': 'application/json',
        }

        response = requests.post(self.valves.API_URL, json=data, headers=headers, stream=True)
        response.raise_for_status()
        return response.iter_lines()


