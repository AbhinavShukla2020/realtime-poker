from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy import select

from .config import Settings
from .database import Account, Base, HandHistory, session_factory
from .game import Street, Table
from .hub import WebSocketHub
from .rooms import RoomManager
from .storage import RedisTableStore, TableStore


class CreateAccount(BaseModel):
    display_name: str = Field(min_length=2, max_length=40)


class CreateTable(BaseModel):
    table_id: str | None = None


class JoinTable(BaseModel):
    player_id: str
    display_name: str
    stack: int = Field(default=1_000, ge=1)


def create_app(settings: Settings | None = None, store: TableStore | None = None) -> FastAPI:
    settings = settings or Settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True) if store is None else None
    rooms = RoomManager(store or RedisTableStore(redis, settings.reconnect_ttl_seconds))
    hub = WebSocketHub()
    engine, sessions = session_factory(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        yield
        if redis is not None:
            await redis.aclose()
        await engine.dispose()

    app = FastAPI(title="Realtime Poker", lifespan=lifespan)

    async def db_session():
        async with sessions() as session:
            yield session

    async def persist_completed_hand(table: Table) -> None:
        if table.street != Street.COMPLETE or table.hand_id is None:
            return
        async with sessions() as session:
            if await session.get(HandHistory, table.hand_id):
                return
            state = table.to_record()
            state["player_ids"] = [player.player_id for player in table.players]
            session.add(
                HandHistory(
                    hand_id=table.hand_id,
                    table_id=table.table_id,
                    player_count=len(table.players),
                    state=state,
                )
            )
            await session.commit()

    @app.post("/accounts", status_code=201)
    async def create_account(body: CreateAccount, session=Depends(db_session)):
        account = Account(display_name=body.display_name)
        session.add(account)
        await session.commit()
        return {"account_id": account.account_id, "display_name": account.display_name}

    @app.get("/accounts/{account_id}/hands")
    async def account_hands(account_id: str, session=Depends(db_session)):
        query = select(HandHistory).where(HandHistory.state["player_ids"].contains([account_id]))
        result = await session.execute(query)
        return [row.state for row in result.scalars()]

    @app.post("/tables", status_code=201)
    async def create_table(body: CreateTable):
        table_id = body.table_id or uuid.uuid4().hex[:10]
        table = await rooms.create(Table(table_id, settings.small_blind, settings.big_blind))
        return table.public_state()

    @app.post("/tables/{table_id}/players", status_code=201)
    async def join_table(table_id: str, body: JoinTable):
        try:
            table = await rooms.update(
                table_id, lambda value: value.join(body.player_id, body.display_name, body.stack)
            )
        except KeyError as error:
            raise HTTPException(404, "table not found") from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
        await hub.broadcast_state(table)
        return table.public_state(body.player_id)

    @app.get("/tables/{table_id}")
    async def table_state(table_id: str, player_id: str | None = None):
        try:
            return (await rooms.get(table_id)).public_state(player_id)
        except KeyError as error:
            raise HTTPException(404, "table not found") from error

    @app.websocket("/ws/{table_id}/{player_id}")
    async def table_socket(socket: WebSocket, table_id: str, player_id: str):
        await hub.connect(table_id, player_id, socket)
        try:
            table = await rooms.get(table_id)
            await socket.send_json({"type": "state", "state": table.public_state(player_id)})
            while True:
                message = await socket.receive_json()
                command = message.get("type")
                try:
                    if command == "start":
                        table = await rooms.update(
                            table_id, lambda value: value.start_hand(message.get("entropy", {}))
                        )
                    elif command == "action":
                        table = await rooms.update(
                            table_id,
                            lambda value: value.act(
                                player_id, message["action"], int(message.get("amount", 0))
                            ),
                        )
                    elif command == "next_street":
                        table = await rooms.update(table_id, lambda value: value.next_street())
                    else:
                        await socket.send_json({"type": "error", "message": "unknown command"})
                        continue
                except ValueError as error:
                    await socket.send_json({"type": "error", "message": str(error)})
                    continue
                await persist_completed_hand(table)
                await hub.broadcast_state(table)
        except (WebSocketDisconnect, KeyError):
            pass
        finally:
            await hub.disconnect(table_id, player_id, socket)

    return app


app = create_app()
