import json
import asyncio
from typing import Annotated, Optional

import asyncpg

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus as quote

from cloudevents.http import CloudEvent
from cloudevents.conversion import to_binary, to_structured
import httpx

OPERATION_MAP = {"INSERT": "created", "UPDATE": "updated", "DELETE": "deleted"}


class CloudEventSettings(BaseSettings):
    k_sink: str
    k_source: Annotated[Optional[str], Field(default="/eoepca/stac")]
    k_type: Annotated[Optional[str], Field(default="org.eoepca.stac")]


class PostgresSettings(BaseSettings):
    pguser: str
    pgpassword: str
    pghost: str
    pgport: int
    pgdatabase: str
    pgstac_item_channel: Annotated[Optional[str], Field(default="pgstac_items")]
    pgstac_collection_channel: Annotated[Optional[str], Field(default="pgstac_collections")]

    @property
    def connection_string(self):
        return f"postgresql://{self.pguser}:{quote(self.pgpassword)}@{self.pghost}:{self.pgport}/{self.pgdatabase}"


class AppSettings(BaseModel):
    postgresql: PostgresSettings = PostgresSettings()
    cloudevent: CloudEventSettings = CloudEventSettings()
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = AppSettings()


async def handle(conn, pid, channel, payload_str):
    payload = json.loads(payload_str)
    ce_attributes = {
        "source": "/eoepca/stac",
        "type": f"{settings.cloudevent.k_type}.item",
        "collection": payload["collection"],
        "datetime": payload["datetime"],
        "operation": OPERATION_MAP[payload["event"]],
        "subject": payload["id"],
    }
    event = CloudEvent(ce_attributes, None)
    async with httpx.AsyncClient() as client:
        headers, data = to_binary(event)
        response = await client.post(
            settings.cloudevent.k_sink, data=data, headers=headers
        )
        response.raise_for_status()


async def run():
    conn = await asyncpg.connect(settings.postgresql.connection_string)
    await conn.add_listener(settings.postgresql.pgstac_item_channel, handle)


    try:
        await asyncio.Future()  # keep thing rolling
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
