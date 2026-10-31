"""Optional integration test against a real ``opencode acp`` agent.

Skipped when OpenCode is not installed.  This test only performs the
handshake and session creation; it never calls a model.
"""

import os
import shutil
import sys

import pytest

_this_dir = os.path.dirname(__file__)
sys.path.insert(0, _this_dir)
for _name in list(sys.modules):
    if _name == "acp" or _name.startswith("acp."):
        del sys.modules[_name]

from acp import SUPPORTED_PROTOCOL_VERSIONS, ACPClient  # noqa: E402


@pytest.mark.skipif(
    shutil.which("opencode") is None,
    reason="opencode CLI is not installed",
)
@pytest.mark.asyncio
async def test_opencode_handshake_and_new_session(tmp_path):
    client = ACPClient(["opencode", "acp"])
    await client.start()
    try:
        init = await client.initialize()
        assert init.protocol_version in SUPPORTED_PROTOCOL_VERSIONS
        assert init.agent_info is not None
        assert init.agent_info.name

        session = await client.new_session(str(tmp_path), mcp_servers=[])
        assert session.session_id
    finally:
        await client.stop()
