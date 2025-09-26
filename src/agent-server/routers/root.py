from fastapi import APIRouter

class Routes:
    router: APIRouter

    def __call__(self, *args, **kwargs):
        return self.router

    def __init__(
            self,
    ):
        self.router = APIRouter()
        self.router.add_api_route("/", self.root, methods=["GET"])

    async def root(self):
        return {"message": "Welcome to the Agent API Server"}