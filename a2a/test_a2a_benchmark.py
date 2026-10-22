"""Benchmark: zerodep a2a vs a2a-protocol."""

import dataclasses
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from a2a import (
    Artifact,
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatus,
)

# Reference library (skip if not installed)
a2a_ref = pytest.importorskip(
    "a2a_protocol.dataclass", reason="a2a-protocol not installed"
)

# ── Test data: zerodep objects ──

ZD_SMALL_MSG = Message(
    message_id="msg-small",
    role=Role.USER,
    parts=[Part(text="Hello, agent!")],
)

ZD_MEDIUM_TASK = Task(
    id="task-medium",
    status=TaskStatus(
        state=TaskState.COMPLETED,
        timestamp="2026-01-01T00:00:00.000Z",
    ),
    context_id="ctx-medium",
    artifacts=[
        Artifact(
            artifact_id=f"art-{i}",
            parts=[Part(text=f"Artifact {i} part {j}") for j in range(3)],
            name=f"artifact-{i}",
            description=f"Description for artifact {i}",
        )
        for i in range(10)
    ],
    history=[
        Message(
            message_id=f"hist-{i}",
            role=Role.USER if i % 2 == 0 else Role.AGENT,
            parts=[Part(text=f"History message {i}")],
        )
        for i in range(5)
    ],
)

ZD_LARGE_TASKS = [
    Task(
        id=f"task-{t}",
        status=TaskStatus(
            state=TaskState.COMPLETED,
            timestamp="2026-01-01T00:00:00.000Z",
        ),
        context_id=f"ctx-{t}",
        artifacts=[
            Artifact(
                artifact_id=f"art-{t}-{a}",
                parts=[Part(text=f"Task {t} artifact {a} content")],
                name=f"output-{a}",
            )
            for a in range(3)
        ],
        history=[
            Message(
                message_id=f"msg-{t}-{m}",
                role=Role.USER if m % 2 == 0 else Role.AGENT,
                parts=[Part(text=f"Task {t} message {m}")],
            )
            for m in range(4)
        ],
    )
    for t in range(50)
]

# ── Test data: reference objects ──

REF_SMALL_MSG = a2a_ref.Message(
    role=a2a_ref.Role.user,
    parts=[a2a_ref.TextPart(text="Hello, agent!")],
)

REF_MEDIUM_TASK = a2a_ref.Task(
    id="task-medium",
    status=a2a_ref.TaskStatus(
        state=a2a_ref.TaskState.completed,
        timestamp="2026-01-01T00:00:00.000Z",
    ),
    sessionId="ctx-medium",
    artifacts=[
        a2a_ref.Artifact(
            parts=[a2a_ref.TextPart(text=f"Artifact {i} part {j}") for j in range(3)],
            name=f"artifact-{i}",
            description=f"Description for artifact {i}",
        )
        for i in range(10)
    ],
    history=[
        a2a_ref.Message(
            role=a2a_ref.Role.user if i % 2 == 0 else a2a_ref.Role.agent,
            parts=[a2a_ref.TextPart(text=f"History message {i}")],
        )
        for i in range(5)
    ],
)

REF_LARGE_TASKS = [
    a2a_ref.Task(
        id=f"task-{t}",
        status=a2a_ref.TaskStatus(
            state=a2a_ref.TaskState.completed,
            timestamp="2026-01-01T00:00:00.000Z",
        ),
        sessionId=f"ctx-{t}",
        artifacts=[
            a2a_ref.Artifact(
                parts=[a2a_ref.TextPart(text=f"Task {t} artifact {a} content")],
                name=f"output-{a}",
            )
            for a in range(3)
        ],
        history=[
            a2a_ref.Message(
                role=a2a_ref.Role.user if m % 2 == 0 else a2a_ref.Role.agent,
                parts=[a2a_ref.TextPart(text=f"Task {t} message {m}")],
            )
            for m in range(4)
        ],
    )
    for t in range(50)
]

# ── Pre-serialized dicts for deserialization benchmarks ──

ZD_SMALL_DICT = ZD_SMALL_MSG.to_dict()
ZD_MEDIUM_DICT = ZD_MEDIUM_TASK.to_dict()
ZD_LARGE_DICTS = [t.to_dict() for t in ZD_LARGE_TASKS]

# ── Pre-serialized JSON for JSON round-trip benchmarks ──

ZD_SMALL_JSON = json.dumps(ZD_SMALL_DICT)
ZD_MEDIUM_JSON = json.dumps(ZD_MEDIUM_DICT)
ZD_LARGE_JSON = json.dumps(ZD_LARGE_DICTS)


# ── Serialization benchmarks ──


class TestSerializeSmall:
    def test_zerodep(self, benchmark):
        benchmark(ZD_SMALL_MSG.to_dict)

    def test_a2a_protocol(self, benchmark):
        benchmark(dataclasses.asdict, REF_SMALL_MSG)


class TestSerializeMedium:
    def test_zerodep(self, benchmark):
        benchmark(ZD_MEDIUM_TASK.to_dict)

    def test_a2a_protocol(self, benchmark):
        benchmark(dataclasses.asdict, REF_MEDIUM_TASK)


class TestSerializeLarge:
    def test_zerodep(self, benchmark):
        benchmark(lambda: [t.to_dict() for t in ZD_LARGE_TASKS])

    def test_a2a_protocol(self, benchmark):
        benchmark(lambda: [dataclasses.asdict(t) for t in REF_LARGE_TASKS])


# ── Deserialization benchmarks ──


class TestDeserializeSmall:
    def test_zerodep(self, benchmark):
        benchmark(Message.from_dict, ZD_SMALL_DICT)

    def test_a2a_protocol(self, benchmark):
        def _deserialize():
            return a2a_ref.Message(
                role=a2a_ref.Role.user,
                parts=[a2a_ref.TextPart(text="Hello, agent!")],
            )

        benchmark(_deserialize)


class TestDeserializeMedium:
    def test_zerodep(self, benchmark):
        benchmark(Task.from_dict, ZD_MEDIUM_DICT)

    def test_a2a_protocol(self, benchmark):
        def _deserialize():
            return a2a_ref.Task(
                id="task-medium",
                status=a2a_ref.TaskStatus(
                    state=a2a_ref.TaskState.completed,
                    timestamp="2026-01-01T00:00:00.000Z",
                ),
                sessionId="ctx-medium",
                artifacts=[
                    a2a_ref.Artifact(
                        parts=[
                            a2a_ref.TextPart(text=f"Artifact {i} part {j}")
                            for j in range(3)
                        ],
                        name=f"artifact-{i}",
                        description=f"Description for artifact {i}",
                    )
                    for i in range(10)
                ],
                history=[
                    a2a_ref.Message(
                        role=(a2a_ref.Role.user if i % 2 == 0 else a2a_ref.Role.agent),
                        parts=[a2a_ref.TextPart(text=f"History message {i}")],
                    )
                    for i in range(5)
                ],
            )

        benchmark(_deserialize)


class TestDeserializeLarge:
    def test_zerodep(self, benchmark):
        benchmark(lambda: [Task.from_dict(d) for d in ZD_LARGE_DICTS])

    def test_a2a_protocol(self, benchmark):
        def _deserialize():
            tasks = []
            for t in range(50):
                tasks.append(
                    a2a_ref.Task(
                        id=f"task-{t}",
                        status=a2a_ref.TaskStatus(
                            state=a2a_ref.TaskState.completed,
                            timestamp="2026-01-01T00:00:00.000Z",
                        ),
                        sessionId=f"ctx-{t}",
                        artifacts=[
                            a2a_ref.Artifact(
                                parts=[
                                    a2a_ref.TextPart(
                                        text=f"Task {t} artifact {a} content"
                                    )
                                ],
                                name=f"output-{a}",
                            )
                            for a in range(3)
                        ],
                        history=[
                            a2a_ref.Message(
                                role=(
                                    a2a_ref.Role.user
                                    if m % 2 == 0
                                    else a2a_ref.Role.agent
                                ),
                                parts=[a2a_ref.TextPart(text=f"Task {t} message {m}")],
                            )
                            for m in range(4)
                        ],
                    )
                )
            return tasks

        benchmark(_deserialize)


# ── JSON round-trip benchmarks ──


class TestJsonRoundTripSmall:
    def test_zerodep(self, benchmark):
        def _round_trip():
            d = ZD_SMALL_MSG.to_dict()
            s = json.dumps(d)
            return Message.from_dict(json.loads(s))

        benchmark(_round_trip)

    def test_a2a_protocol(self, benchmark):
        def _round_trip():
            d = dataclasses.asdict(REF_SMALL_MSG)
            s = json.dumps(d, default=str)
            return json.loads(s)

        benchmark(_round_trip)


class TestJsonRoundTripMedium:
    def test_zerodep(self, benchmark):
        def _round_trip():
            d = ZD_MEDIUM_TASK.to_dict()
            s = json.dumps(d)
            return Task.from_dict(json.loads(s))

        benchmark(_round_trip)

    def test_a2a_protocol(self, benchmark):
        def _round_trip():
            d = dataclasses.asdict(REF_MEDIUM_TASK)
            s = json.dumps(d, default=str)
            return json.loads(s)

        benchmark(_round_trip)


class TestJsonRoundTripLarge:
    def test_zerodep(self, benchmark):
        def _round_trip():
            dicts = [t.to_dict() for t in ZD_LARGE_TASKS]
            s = json.dumps(dicts)
            return [Task.from_dict(d) for d in json.loads(s)]

        benchmark(_round_trip)

    def test_a2a_protocol(self, benchmark):
        def _round_trip():
            dicts = [dataclasses.asdict(t) for t in REF_LARGE_TASKS]
            s = json.dumps(dicts, default=str)
            return json.loads(s)

        benchmark(_round_trip)
