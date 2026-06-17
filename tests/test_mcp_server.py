from __future__ import annotations

import unittest

from control_promotion_mcp.server import ControlPromotionMCP, PROTOCOL_VERSION


class MCPServerTest(unittest.TestCase):
    def test_initialize(self) -> None:
        server = ControlPromotionMCP(".")
        response = server.handle(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": PROTOCOL_VERSION},
            }
        )
        self.assertIsNotNone(response)
        self.assertEqual(response["result"]["protocolVersion"], PROTOCOL_VERSION)
        self.assertIn("tools", response["result"]["capabilities"])

    def test_tool_call_returns_structured_content(self) -> None:
        server = ControlPromotionMCP(".")
        response = server.handle(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "route_control_destination",
                    "arguments": {
                        "failure_class": "semantic metric literal",
                        "detectability": "static",
                        "recurrence": "repeated",
                        "harm": "high",
                    },
                },
            }
        )
        self.assertIsNotNone(response)
        content = response["result"]["structuredContent"]
        self.assertEqual(content["destination"], "scripts/quality")

    def test_resources_list(self) -> None:
        server = ControlPromotionMCP(".")
        response = server.handle({"jsonrpc": "2.0", "id": 3, "method": "resources/list"})
        self.assertIsNotNone(response)
        uris = {item["uri"] for item in response["result"]["resources"]}
        self.assertIn("control://ladder", uris)
        self.assertIn("adapter://project", uris)
        self.assertIn("schema://guard-spec", uris)

    def test_validate_guard_spec_tool(self) -> None:
        server = ControlPromotionMCP(".")
        response = server.handle(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "validate_guard_spec",
                    "arguments": {"path": "examples/guard-specs/good-creation-table-contract.yaml"},
                },
            }
        )
        self.assertIsNotNone(response)
        content = response["result"]["structuredContent"]
        self.assertTrue(content["valid"])


if __name__ == "__main__":
    unittest.main()
