#!/usr/bin/env python3
"""Minimal test agent for AIKworkw marketplace."""

import os
import sys
import time

import httpx

API_BASE = os.getenv("AIKWORKW_API", "http://localhost:8000/api/v1")
API_KEY = os.getenv("AGENT_API_KEY", "")

if not API_KEY:
    print("Set AGENT_API_KEY environment variable")
    sys.exit(1)

headers = {"Authorization": f"Bearer {API_KEY}"}


def poll_tasks(client: httpx.Client) -> list[dict]:
    resp = client.get(f"{API_BASE}/agent/tasks/poll", headers=headers)
    resp.raise_for_status()
    return resp.json().get("tasks", [])


def handle_task(client: httpx.Client, task: dict) -> None:
    task_id = task["task_id"]
    task_type = task["type"]
    print(f"Task {task_id} type={task_type}")

    if task_type == "estimate_requested":
        client.post(
            f"{API_BASE}/agent/tasks/{task_id}/estimate",
            headers=headers,
            json={
                "price": 15000,
                "deadline_hours": 48,
                "confidence": 0.9,
                "message": "Авто-оценка от test-agent",
                "questions": [],
            },
        ).raise_for_status()
        print("  -> estimate submitted")

    elif task_type == "assigned":
        client.post(
            f"{API_BASE}/agent/tasks/{task_id}/accept",
            headers=headers,
        ).raise_for_status()
        client.post(
            f"{API_BASE}/agent/tasks/{task_id}/status",
            headers=headers,
            json={"status": "in_progress", "progress": 50, "message": "Working..."},
        ).raise_for_status()
        client.post(
            f"{API_BASE}/agent/tasks/{task_id}/result",
            headers=headers,
            json={"text": "Работа выполнена test-agent", "files": []},
        ).raise_for_status()
        print("  -> result submitted")

    elif task_type == "agent.test_requested":
        print("  -> test task received")

    elif task_type == "revision_requested":
        client.post(
            f"{API_BASE}/agent/tasks/{task_id}/result",
            headers=headers,
            json={"text": "Доработка выполнена", "files": []},
        ).raise_for_status()
        print("  -> revision submitted")


def main() -> None:
    print(f"Test agent polling {API_BASE}")
    with httpx.Client(timeout=30.0) as client:
        while True:
            try:
                tasks = poll_tasks(client)
                for task in tasks:
                    handle_task(client, task)
            except Exception as exc:
                print(f"Error: {exc}")
            time.sleep(3)


if __name__ == "__main__":
    main()
