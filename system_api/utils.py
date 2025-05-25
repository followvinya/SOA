import httpx
from fastapi import HTTPException
import os

# User service URL
#USER_SERVICE_URL = "http://localhost:8001"
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")


async def make_request(method, endpoint, json=None, headers=None):
    url = f"{USER_SERVICE_URL}{endpoint}"

    # this is my debug
    print(f"Making {method} request to {url}")
    print(f"Headers: {headers}")
    print(f"JSON data: {json}")

    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=json, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=json, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # my debug
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

            response.raise_for_status()
            return response.json() if response.content else None

        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code}, {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.json() if e.response.content else str(e)
            )
        except httpx.RequestError as e:  # connection error
            print(f"Request error: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
