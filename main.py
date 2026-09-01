"""
Legacy compatibility shim for CivicSync.

The app no longer relies on a Python FastAPI backend. It runs directly in the
browser and writes complaint data to Firebase Firestore. This file is kept as a
minimal ASGI app so `uvicorn main:app` does not crash if someone starts it by
mistake.
"""


class App:
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return

        body = (
            b'{"status":"ok","message":"FastAPI backend removed. The app now '
            b'works directly in the browser with Firebase."}'
        )
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


app = App()