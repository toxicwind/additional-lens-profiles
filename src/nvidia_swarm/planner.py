#!/usr/bin/env python3
"""
NVIDIA Swarm Planner — Dependency-aware planning with codebase research
Inspired by: am-will/swarms (swarm-planner skill)
Credit: https://github.com/am-will/swarms
"""

import json, re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class PlanTask:
    """A single task in the execution plan."""
    id: str
    description: str
    agent_type: str  # researcher, analyst, coder, etc.
    dependencies: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    estimated_tokens: int = 2048
    output_format: str = "text"
    validation_criteria: List[str] = field(default_factory=list)

@dataclass
class SwarmPlan:
    """A complete execution plan for a swarm task."""
    task_id: str
    title: str
    description: str
    tasks: List[PlanTask]
    waves: List[List[str]]  # Task IDs grouped by wave (parallel execution)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "waves": self.waves,
            "tasks": [{"id": t.id, "description": t.description, "agent_type": t.agent_type,
                       "dependencies": t.dependencies, "tools": t.tools} for t in self.tasks],
        }, indent=2)

class SwarmPlanner:
    """Plans swarm execution by analyzing task complexity and agent capabilities.

    Borrowed patterns:
    - Wave-based execution from am-will/swarms
    - Dependency ordering from ruvnet/agentic-flow
    - Task decomposition from qodex-ai/ai-agent-skills
    """

    def __init__(self, lens_registry: Dict[str, Any]):
        self.lens_registry = lens_registry

    def plan(self, task_description: str, context: Dict[str, Any] = None) -> SwarmPlan:
        """Generate an execution plan for the given task."""
        context = context or {}

        # Analyze task to determine required agents and dependencies
        plan = SwarmPlan(
            task_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=task_description[:60],
            description=task_description,
            tasks=[],
            waves=[],
            context=context,
        )

        # Decompose into subtasks based on task type
        if "research" in task_description.lower() or "find" in task_description.lower():
            plan.tasks = self._plan_research_task(task_description, context)
        elif "code" in task_description.lower() or "build" in task_description.lower():
            plan.tasks = self._plan_coding_task(task_description, context)
        elif "analyze" in task_description.lower() or "benchmark" in task_description.lower():
            plan.tasks = self._plan_analysis_task(task_description, context)
        else:
            plan.tasks = self._plan_generic_task(task_description, context)

        # Build waves from dependencies
        plan.waves = self._build_waves(plan.tasks)
        return plan

    def _plan_research_task(self, task: str, ctx: Dict) -> List[PlanTask]:
        return [
            PlanTask(id="T1", description=f"Search for information: {task}", 
                    agent_type="researcher", tools=["web_search", "web_open_url"],
                    validation_criteria=["At least 3 sources found", "Sources are authoritative"]),
            PlanTask(id="T2", description="Analyze and synthesize findings", 
                    agent_type="analyst", dependencies=["T1"], tools=["ipython"],
                    validation_criteria=["Key insights extracted", "Contradictions noted"]),
            PlanTask(id="T3", description="Generate structured report", 
                    agent_type="coder", dependencies=["T2"], tools=["write_file"],
                    output_format="markdown", validation_criteria=["Report is structured", "Sources cited"]),
        ]

    def _plan_coding_task(self, task: str, ctx: Dict) -> List[PlanTask]:
        return [
            PlanTask(id="T1", description=f"Research existing solutions for: {task}", 
                    agent_type="researcher", tools=["web_search"]),
            PlanTask(id="T2", description="Design architecture and API", 
                    agent_type="analyst", dependencies=["T1"], tools=["ipython"]),
            PlanTask(id="T3", description="Implement core functionality", 
                    agent_type="coder", dependencies=["T2"], tools=["ipython", "write_file"]),
            PlanTask(id="T4", description="Write tests and validate", 
                    agent_type="coder", dependencies=["T3"], tools=["ipython"]),
        ]

    def _plan_analysis_task(self, task: str, ctx: Dict) -> List[PlanTask]:
        return [
            PlanTask(id="T1", description=f"Gather data for: {task}", 
                    agent_type="researcher", tools=["get_data_source", "web_search"]),
            PlanTask(id="T2", description="Process and clean data", 
                    agent_type="analyst", dependencies=["T1"], tools=["ipython"]),
            PlanTask(id="T3", description="Run analysis and generate visualizations", 
                    agent_type="analyst", dependencies=["T2"], tools=["ipython"]),
            PlanTask(id="T4", description="Interpret results and recommend actions", 
                    agent_type="analyst", dependencies=["T3"]),
        ]

    def _plan_generic_task(self, task: str, ctx: Dict) -> List[PlanTask]:
        return [
            PlanTask(id="T1", description=f"Understand requirements: {task}", 
                    agent_type="researcher"),
            PlanTask(id="T2", description="Develop approach", 
                    agent_type="analyst", dependencies=["T1"]),
            PlanTask(id="T3", description="Execute and deliver", 
                    agent_type="coder", dependencies=["T2"]),
        ]

    def _build_waves(self, tasks: List[PlanTask]) -> List[List[str]]:
        """Build execution waves from task dependencies.
        Tasks in the same wave can run in parallel."""
        completed = set()
        waves = []
        pending = {t.id: t for t in tasks}

        while pending:
            ready = [tid for tid, t in pending.items() if all(d in completed for d in t.dependencies)]
            if not ready:
                raise ValueError("Circular dependencies detected")
            waves.append(ready)
            for tid in ready:
                completed.add(tid)
                del pending[tid]

        return waves
