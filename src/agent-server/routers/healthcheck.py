from fastapi import APIRouter

class Routes:
    router: APIRouter

    def __call__(self, *args, **kwargs):
        return self.router

    def __init__(
            self,
    ):
        self.router = APIRouter()
        self.router.add_api_route("/healthcheck", self.healthcheck, methods=["GET"])

    async def healthcheck(self):
        return {
            "status": "ok"
        }
