"""Agent retry pacing, error attribution and event-loop responsiveness."""
import asyncio
import threading
import unittest
from unittest.mock import patch

import httpx

from atlasguard import agent
from atlasguard.models import HostSnapshot

HOST = HostSnapshot(hostname="qa", cpu_percent=0, memory_percent=1,
                    load_1m=0, process_count=1, established_tcp=0)
REAL_CLIENT = httpx.AsyncClient


class AgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_delivery_errors_are_logged_and_next_sample_recovers(self):
        requests = []
        def handle(request):
            requests.append(request)
            if len(requests) == 1:
                raise httpx.ConnectError("private controller detail", request=request)
            return httpx.Response((429, 500, 200)[len(requests) - 2])
        client = REAL_CLIENT(transport=httpx.MockTransport(handle))
        async def pause(_interval):
            if len(requests) == 4:
                raise asyncio.CancelledError
        with patch.object(agent.httpx, "AsyncClient", return_value=client), \
             patch.object(agent, "collect_host_snapshot", return_value=HOST), \
             patch.object(agent.asyncio, "sleep", side_effect=pause) as sleep, \
             self.assertLogs(agent.logger, level="WARNING") as logs, \
             self.assertRaises(asyncio.CancelledError):
            await agent.run_agent("http://controller", interval_seconds=2)
        self.assertEqual(len(requests), 4)
        self.assertEqual(sleep.await_count, 4)
        self.assertTrue(all(call.args == (2,) for call in sleep.await_args_list))
        self.assertEqual(len(logs.output), 3)
        self.assertIn("ConnectError", logs.output[0])
        self.assertIn("HTTPStatusError", logs.output[1])
        self.assertNotIn("private controller detail", str(logs.output))
        self.assertTrue(client.is_closed)

    async def test_collection_failure_is_paced_and_recovers(self):
        client = REAL_CLIENT(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
        pauses = 0
        async def pause(_interval):
            nonlocal pauses
            pauses += 1
            if pauses == 2:
                raise asyncio.CancelledError
        with patch.object(agent.httpx, "AsyncClient", return_value=client), \
             patch.object(agent, "collect_host_snapshot", side_effect=[OSError("private path"), HOST]) as collect, \
             patch.object(agent.asyncio, "sleep", side_effect=pause), \
             self.assertLogs(agent.logger, level="WARNING") as logs, \
             self.assertRaises(asyncio.CancelledError):
            await agent.run_agent("http://controller", interval_seconds=1)
        self.assertEqual(collect.call_count, 2)
        self.assertEqual(pauses, 2)
        self.assertIn("Host collection failed (OSError)", logs.output[0])
        self.assertNotIn("private path", str(logs.output))
        self.assertTrue(client.is_closed)

    async def test_snapshot_runs_off_event_loop_and_cancellation_closes_client(self):
        loop_thread = threading.get_ident()
        sampled_threads = []
        def collect():
            sampled_threads.append(threading.get_ident())
            return HOST
        requested = asyncio.Event()
        async def handle(request):
            requested.set()
            await asyncio.Event().wait()
        client = REAL_CLIENT(transport=httpx.MockTransport(handle))
        with patch.object(agent.httpx, "AsyncClient", return_value=client), \
             patch.object(agent, "collect_host_snapshot", side_effect=collect):
            task = asyncio.create_task(agent.run_agent("http://controller"))
            await asyncio.wait_for(requested.wait(), 2)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertEqual(len(sampled_threads), 1)
        self.assertNotEqual(sampled_threads[0], loop_thread)
        self.assertTrue(client.is_closed)

    async def test_invalid_options_fail_before_network_or_collection(self):
        with patch.object(agent.httpx, "AsyncClient") as client, \
             patch.object(agent, "collect_host_snapshot") as collect:
            for interval in (0, -1, True, float("nan"), float("inf"), 3601):
                with self.subTest(interval=interval), self.assertRaises(ValueError):
                    await agent.run_agent("http://controller", interval_seconds=interval)
            for url in ("controller", "file:///tmp/controller", "ftp://controller", "http://"):
                with self.subTest(url=url), self.assertRaises(ValueError):
                    await agent.run_agent(url)
            client.assert_not_called()
            collect.assert_not_called()
