"""Browser Visualizer for simulated runs (serves http://127.0.0.1:<fs_port>/)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from . import compat

log = logging.getLogger(__name__)

DEFAULT_FS_PORT = 1337  # HTTP page
DEFAULT_WS_PORT = 2121  # websocket the page connects to


@asynccontextmanager
async def visualize(
  resource: compat.LiquidHandler,
  enabled: bool = True,
  open_browser: bool = True,
  fs_port: int = DEFAULT_FS_PORT,
  ws_port: int = DEFAULT_WS_PORT,
  host: str = "127.0.0.1",
) -> AsyncIterator[compat.Visualizer | None]:
  """Run a Visualizer for the duration of the block. No-op (yields None) when disabled.

  Start it AFTER `lh.setup()` so the page reflects the set-up deck.
  """
  if not enabled:
    yield None
    return
  vis = compat.Visualizer(
    resource=resource, host=host, ws_port=ws_port, fs_port=fs_port, open_browser=open_browser
  )
  await vis.setup()
  log.info("Visualizer at http://%s:%d/", host, fs_port)
  try:
    yield vis
  finally:
    await vis.stop()
