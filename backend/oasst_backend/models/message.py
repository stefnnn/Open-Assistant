from datetime import datetime
from http import HTTPStatus
from typing import Optional
from uuid import UUID, uuid4

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg
from oasst_backend.models.db_payload import MessagePayload
from oasst_shared.exceptions.oasst_api_error import OasstError, OasstErrorCode
from sqlalchemy import false
from sqlmodel import Field, Index, SQLModel

from .payload_column_type import PayloadContainer, payload_column_type


class Message(SQLModel, table=True):
    __tablename__ = "message"
    __table_args__ = (Index("ix_message_frontend_message_id", "api_client_id", "frontend_message_id", unique=True),)

    id: Optional[UUID] = Field(
        sa_column=sa.Column(
            pg.UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=sa.text("gen_random_uuid()")
        ),
    )
    parent_id: Optional[UUID] = Field(nullable=True)
    message_tree_id: UUID = Field(nullable=False, index=True)
    task_id: Optional[UUID] = Field(nullable=True, index=True)
    user_id: Optional[UUID] = Field(nullable=True, foreign_key="user.id", index=True)
    role: str = Field(nullable=False, max_length=128, regex="^prompter|assistant$")
    api_client_id: UUID = Field(nullable=False, foreign_key="api_client.id")
    frontend_message_id: str = Field(max_length=200, nullable=False)
    created_date: Optional[datetime] = Field(
        sa_column=sa.Column(sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp())
    )
    payload_type: str = Field(nullable=False, max_length=200)
    payload: Optional[PayloadContainer] = Field(
        sa_column=sa.Column(payload_column_type(PayloadContainer), nullable=True)
    )
    lang: str = Field(nullable=False, max_length=200, default="en-US")
    depth: int = Field(sa_column=sa.Column(sa.Integer, default=0, server_default=sa.text("0"), nullable=False))
    children_count: int = Field(sa_column=sa.Column(sa.Integer, default=0, server_default=sa.text("0"), nullable=False))
    deleted: bool = Field(sa_column=sa.Column(sa.Boolean, nullable=False, server_default=false()))

    def ensure_is_message(self) -> None:
        if not self.payload or not isinstance(self.payload.payload, MessagePayload):
            raise OasstError("Invalid message", OasstErrorCode.INVALID_MESSAGE, HTTPStatus.INTERNAL_SERVER_ERROR)

    @property
    def text(self) -> str:
        self.ensure_is_message()
        return self.payload.payload.text
