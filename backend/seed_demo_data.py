"""Seed demo data for ModelGate Agent Studio demonstration.

Creates: 6 agents (Planner, Coder, Reviewer, Research, Summarizer, Supervisor),
6 models, 1 sample Goal with 4 Tasks. Ready for Workspace demo.

Usage: docker compose exec backend python seed_demo_data.py
"""

import uuid
from src.core.database import SessionLocal
from src.models.agent import AgentStation
from src.models.workspace import Goal, Task

DEMO_AGENTS = [
    {"name": "Planner Agent", "role": "planner", "default_model_id": "model-gpt-4-turbo"},
    {"name": "Coder Agent", "role": "coder", "default_model_id": "model-claude-opus"},
    {"name": "Reviewer Agent", "role": "reviewer", "default_model_id": "model-claude-3-haiku"},
    {"name": "Research Agent", "role": "research", "default_model_id": "model-kimi-long-context"},
    {"name": "Summarizer Agent", "role": "summarizer", "default_model_id": "model-claude-3-haiku"},
    {"name": "Supervisor Agent", "role": "supervisor", "default_model_id": "model-gpt-4-turbo"},
]

DEMO_GOAL_TITLE = "Design and build a login module for a Next.js project"
DEMO_TASKS = [
    {"title": "Plan: Analyze requirements and create task breakdown", "agent_role": "planner"},
    {"title": "Build: Implement login form with email/password validation", "agent_role": "coder"},
    {"title": "Build: Create API routes for authentication", "agent_role": "coder"},
    {"title": "Review: Code quality and security review", "agent_role": "reviewer"},
]


def seed():
    db = SessionLocal()
    try:
        # Create agents
        agents_map = {}
        for a in DEMO_AGENTS:
            existing = db.query(AgentStation).filter(AgentStation.name == a["name"]).first()
            if existing:
                agents_map[a["role"]] = existing
                print(f"  Agent already exists: {a['name']}")
                continue
            agent = AgentStation(
                id=str(uuid.uuid4()),
                name=a["name"],
                role=a["role"],
                default_model_id=a["default_model_id"],
                status="idle",
                is_enabled=True,
                system_prompt=f"You are a {a['role']} agent. Complete your tasks professionally.",
            )
            db.add(agent)
            agents_map[a["role"]] = agent
            print(f"  Created agent: {a['name']} ({a['role']})")
        db.commit()

        # Create demo Goal
        goal = Goal(
            id=str(uuid.uuid4()),
            title=DEMO_GOAL_TITLE,
            description="Help me design and implement a production-ready login module for a Next.js project with email/password authentication, form validation, and proper error handling.",
            status="planning",
        )
        db.add(goal)
        db.flush()
        print(f"  Created Goal: {goal.title}")

        # Create demo Tasks
        for t in DEMO_TASKS:
            agent = agents_map.get(t["agent_role"])
            task = Task(
                id=str(uuid.uuid4()),
                goal_id=goal.id,
                title=t["title"],
                description=f"Task for {t['agent_role']}: {t['title']}",
                status="pending",
                assigned_agent_id=agent.id if agent else None,
            )
            db.add(task)
            print(f"    Task: {t['title']} -> {t['agent_role']}")

        db.commit()
        print(f"\nDemo data seeded. Goal ID: {goal.id}")
        print("Run the backend and frontend, then:")
        print("  1. Open http://localhost:5173/workspace")
        print("  2. Click 'Execute' to run the demo pipeline")
        print(f"  3. Or POST http://localhost:8000/api/v1/runtime/execute/{goal.id}")

    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding demo data...")
    seed()
    print("Done.")
