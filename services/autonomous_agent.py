"""
Autonomous Agent System for Goal-Oriented Planning and Execution
================================================================

This module implements autonomous reasoning and decision-making capabilities:
- Goal decomposition and planning
- Multi-step task execution 
- Dynamic replanning based on feedback
- Tool orchestration and workflow management
- Context-aware decision making
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from services.llm_service import llm_service
from services.tool_service import tool_service
from services.database_manager import db_manager
from memory.api.enhanced_memory_api import EnhancedMemoryAPI
from core.unified_logging import get_logger, log_service_status
from utilities.simple_error_handling import handle_service_errors


class TaskStatus(Enum):
    """Status of autonomous tasks."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"


class ExecutionStrategy(Enum):
    """Different execution strategies for autonomous tasks."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ADAPTIVE = "adaptive"


@dataclass
class Goal:
    """Represents a high-level goal to be achieved."""
    goal_id: str
    description: str
    user_id: str
    priority: int = 1  # 1-10, higher = more important
    deadline: Optional[datetime] = None
    success_criteria: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Task:
    """Represents a specific task in pursuit of a goal."""
    task_id: str
    goal_id: str
    description: str
    action_type: str  # "tool_call", "llm_query", "memory_search", "validation"
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # task_ids that must complete first
    status: TaskStatus = TaskStatus.PLANNED
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ExecutionPlan:
    """Complete execution plan for achieving a goal."""
    plan_id: str
    goal_id: str
    tasks: List[Task]
    strategy: ExecutionStrategy
    estimated_duration: Optional[int] = None  # seconds
    confidence_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class AutonomousPlanner:
    """Plans task sequences to achieve goals."""
    
    def __init__(self, llm_service, memory_api: EnhancedMemoryAPI):
        self.llm_service = llm_service
        self.memory_api = memory_api
        self.logger = get_logger(__name__)
        
    async def create_execution_plan(self, goal: Goal) -> ExecutionPlan:
        """Create an execution plan to achieve the goal."""
        try:
            # 1. Analyze the goal and break it down
            decomposition = await self._decompose_goal(goal)
            
            # 2. Create specific tasks
            tasks = await self._create_tasks(goal, decomposition)
            
            # 3. Determine optimal execution strategy
            strategy = await self._determine_strategy(goal, tasks)
            
            # 4. Calculate confidence and duration estimates
            confidence = await self._calculate_confidence(goal, tasks)
            duration = await self._estimate_duration(tasks)
            
            plan = ExecutionPlan(
                plan_id=str(uuid4()),
                goal_id=goal.goal_id,
                tasks=tasks,
                strategy=strategy,
                estimated_duration=duration,
                confidence_score=confidence
            )
            
            log_service_status("AUTONOMOUS", "info", 
                             f"Created execution plan with {len(tasks)} tasks for goal: {goal.description[:50]}...")
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Failed to create execution plan: {e}")
            raise
    
    async def _decompose_goal(self, goal: Goal) -> Dict[str, Any]:
        """Break down a complex goal into manageable components."""
        decomposition_prompt = f"""
        Analyze this goal and break it down into logical steps:
        
        Goal: {goal.description}
        Context: {json.dumps(goal.context, indent=2)}
        Success Criteria: {goal.success_criteria}
        
        Break this down into:
        1. Required information gathering steps
        2. Tool operations needed  
        3. Decision points
        4. Validation steps
        5. Dependencies between steps
        
        Respond with a JSON structure containing the decomposition.
        """
        
        messages = [{"role": "user", "content": decomposition_prompt}]
        response = await self.llm_service.call_llm(messages)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback to basic decomposition
            return {
                "steps": [goal.description],
                "tools": [],
                "dependencies": [],
                "validation": ["Verify goal completion"]
            }
    
    async def _create_tasks(self, goal: Goal, decomposition: Dict[str, Any]) -> List[Task]:
        """Create specific tasks from goal decomposition."""
        tasks = []
        task_counter = 0
        
        # Create information gathering tasks
        for step in decomposition.get("information_gathering", []):
            task_counter += 1
            task = Task(
                task_id=f"{goal.goal_id}_task_{task_counter}",
                goal_id=goal.goal_id,
                description=step,
                action_type="memory_search",
                parameters={"query": step, "max_results": 5}
            )
            tasks.append(task)
        
        # Create tool execution tasks
        for tool_op in decomposition.get("tools", []):
            task_counter += 1
            task = Task(
                task_id=f"{goal.goal_id}_task_{task_counter}",
                goal_id=goal.goal_id,
                description=tool_op.get("description", "Tool operation"),
                action_type="tool_call",
                parameters=tool_op.get("parameters", {})
            )
            tasks.append(task)
        
        # Create validation tasks
        for validation in decomposition.get("validation", []):
            task_counter += 1
            task = Task(
                task_id=f"{goal.goal_id}_task_{task_counter}",
                goal_id=goal.goal_id,
                description=validation,
                action_type="validation",
                parameters={"criteria": validation}
            )
            tasks.append(task)
        
        return tasks
    
    async def _determine_strategy(self, goal: Goal, tasks: List[Task]) -> ExecutionStrategy:
        """Determine the optimal execution strategy."""
        # Simple heuristics for now - can be made more sophisticated
        if len(tasks) <= 2:
            return ExecutionStrategy.SEQUENTIAL
        
        # Check for independent tasks that can run in parallel
        has_dependencies = any(task.dependencies for task in tasks)
        if not has_dependencies and len(tasks) <= 5:
            return ExecutionStrategy.PARALLEL
        
        # Default to adaptive for complex scenarios
        return ExecutionStrategy.ADAPTIVE
    
    async def _calculate_confidence(self, goal: Goal, tasks: List[Task]) -> float:
        """Calculate confidence in the execution plan."""
        # Base confidence on task complexity and available tools
        base_confidence = 0.7
        
        # Adjust based on task types
        tool_tasks = sum(1 for task in tasks if task.action_type == "tool_call")
        if tool_tasks > 0:
            base_confidence += 0.1  # Tool usage increases confidence
        
        # Adjust based on goal complexity
        if len(tasks) > 5:
            base_confidence -= 0.1  # More complex plans are less certain
        
        return min(max(base_confidence, 0.0), 1.0)
    
    async def _estimate_duration(self, tasks: List[Task]) -> int:
        """Estimate execution duration in seconds."""
        # Simple estimation based on task types
        duration = 0
        for task in tasks:
            if task.action_type == "tool_call":
                duration += 10  # Tool calls take ~10 seconds
            elif task.action_type == "memory_search":
                duration += 5   # Memory searches take ~5 seconds
            elif task.action_type == "llm_query":
                duration += 15  # LLM calls take ~15 seconds
            else:
                duration += 5   # Other tasks take ~5 seconds
        
        return duration


class AutonomousExecutor:
    """Executes autonomous plans and manages task orchestration."""
    
    def __init__(self, llm_service, tool_service, memory_api: EnhancedMemoryAPI):
        self.llm_service = llm_service
        self.tool_service = tool_service
        self.memory_api = memory_api
        self.logger = get_logger(__name__)
        self.active_executions: Dict[str, ExecutionPlan] = {}
        
    async def execute_plan(self, plan: ExecutionPlan, user_id: str) -> Dict[str, Any]:
        """Execute an autonomous plan."""
        try:
            self.active_executions[plan.plan_id] = plan
            
            log_service_status("AUTONOMOUS", "info", 
                             f"Starting execution of plan {plan.plan_id} with {len(plan.tasks)} tasks")
            
            # Execute based on strategy
            if plan.strategy == ExecutionStrategy.SEQUENTIAL:
                results = await self._execute_sequential(plan, user_id)
            elif plan.strategy == ExecutionStrategy.PARALLEL:
                results = await self._execute_parallel(plan, user_id)
            elif plan.strategy == ExecutionStrategy.ADAPTIVE:
                results = await self._execute_adaptive(plan, user_id)
            else:
                results = await self._execute_sequential(plan, user_id)  # fallback
            
            # Compile final results
            execution_summary = {
                "plan_id": plan.plan_id,
                "goal_id": plan.goal_id,
                "status": "completed",
                "tasks_completed": sum(1 for task in plan.tasks if task.status == TaskStatus.COMPLETED),
                "tasks_failed": sum(1 for task in plan.tasks if task.status == TaskStatus.FAILED),
                "total_tasks": len(plan.tasks),
                "results": results,
                "execution_time": sum((task.completed_at - task.started_at).total_seconds() 
                                    for task in plan.tasks if task.started_at and task.completed_at)
            }
            
            # Store execution results in memory for future learning
            await self._store_execution_results(execution_summary, user_id)
            
            return execution_summary
            
        except Exception as e:
            self.logger.error(f"Plan execution failed: {e}")
            return {
                "plan_id": plan.plan_id,
                "status": "failed",
                "error": str(e)
            }
        finally:
            # Cleanup
            if plan.plan_id in self.active_executions:
                del self.active_executions[plan.plan_id]
    
    async def _execute_sequential(self, plan: ExecutionPlan, user_id: str) -> List[Any]:
        """Execute tasks sequentially."""
        results = []
        
        for task in plan.tasks:
            if await self._check_dependencies(task, plan.tasks):
                result = await self._execute_task(task, user_id)
                results.append(result)
            else:
                task.status = TaskStatus.FAILED
                task.error = "Dependencies not met"
                results.append(None)
        
        return results
    
    async def _execute_parallel(self, plan: ExecutionPlan, user_id: str) -> List[Any]:
        """Execute independent tasks in parallel."""
        # Group tasks by dependency level
        dependency_levels = self._analyze_dependencies(plan.tasks)
        results = []
        
        for level_tasks in dependency_levels:
            # Execute all tasks at this level in parallel
            level_results = await asyncio.gather(
                *[self._execute_task(task, user_id) for task in level_tasks],
                return_exceptions=True
            )
            results.extend(level_results)
        
        return results
    
    async def _execute_adaptive(self, plan: ExecutionPlan, user_id: str) -> List[Any]:
        """Execute with dynamic adaptation based on results."""
        results = []
        completed_tasks = set()
        
        while len(completed_tasks) < len(plan.tasks):
            # Find ready tasks (dependencies satisfied)
            ready_tasks = [
                task for task in plan.tasks 
                if (task.task_id not in completed_tasks and 
                    all(dep in completed_tasks for dep in task.dependencies))
            ]
            
            if not ready_tasks:
                break  # No more executable tasks
            
            # Execute ready tasks
            for task in ready_tasks:
                result = await self._execute_task(task, user_id)
                results.append(result)
                completed_tasks.add(task.task_id)
                
                # Adaptive decision: should we continue or replan?
                if task.status == TaskStatus.FAILED and task.retry_count >= task.max_retries:
                    # Critical failure - might need to replan
                    should_continue = await self._decide_continuation(task, plan, user_id)
                    if not should_continue:
                        break
        
        return results
    
    async def _execute_task(self, task: Task, user_id: str) -> Any:
        """Execute a single task."""
        try:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            log_service_status("AUTONOMOUS", "info", f"Executing task: {task.description}")
            
            if task.action_type == "tool_call":
                result = await self._execute_tool_task(task, user_id)
            elif task.action_type == "memory_search":
                result = await self._execute_memory_task(task, user_id)
            elif task.action_type == "llm_query":
                result = await self._execute_llm_task(task, user_id)
            elif task.action_type == "validation":
                result = await self._execute_validation_task(task, user_id)
            else:
                raise ValueError(f"Unknown task type: {task.action_type}")
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PLANNED
                self.logger.warning(f"Task failed, retrying ({task.retry_count}/{task.max_retries}): {e}")
                return await self._execute_task(task, user_id)
            
            self.logger.error(f"Task failed permanently: {e}")
            return None
    
    async def _execute_tool_task(self, task: Task, user_id: str) -> Any:
        """Execute a tool-based task."""
        # Convert task to tool service call
        message = task.description
        tool_used, tool_response, tool_name, debug_info = self.tool_service.detect_and_execute_tool(
            message, user_id, task.task_id
        )
        
        if tool_used:
            return {
                "tool_name": tool_name,
                "response": tool_response,
                "debug_info": debug_info
            }
        else:
            raise Exception("No suitable tool found for task")
    
    async def _execute_memory_task(self, task: Task, user_id: str) -> Any:
        """Execute a memory search task."""
        query = task.parameters.get("query", task.description)
        max_results = task.parameters.get("max_results", 5)
        
        memories = await self.memory_api.search_memories(
            user_id=user_id,
            query=query,
            limit=max_results,
            threshold=0.7
        )
        
        return {
            "query": query,
            "memories_found": len(memories),
            "memories": memories
        }
    
    async def _execute_llm_task(self, task: Task, user_id: str) -> Any:
        """Execute an LLM reasoning task."""
        prompt = task.parameters.get("prompt", task.description)
        context = task.parameters.get("context", "")
        
        full_prompt = f"Context: {context}\n\nTask: {prompt}"
        messages = [{"role": "user", "content": full_prompt}]
        
        response = await self.llm_service.call_llm(messages)
        
        return {
            "prompt": prompt,
            "response": response
        }
    
    async def _execute_validation_task(self, task: Task, user_id: str) -> Any:
        """Execute a validation task."""
        criteria = task.parameters.get("criteria", task.description)
        
        # Use LLM to perform validation reasoning
        validation_prompt = f"""
        Validate whether the following criteria has been met:
        Criteria: {criteria}
        
        Based on the context and previous task results, determine if this criteria is satisfied.
        Respond with: VALIDATED or NOT_VALIDATED, followed by your reasoning.
        """
        
        messages = [{"role": "user", "content": validation_prompt}]
        response = await self.llm_service.call_llm(messages)
        
        is_validated = "VALIDATED" in response and "NOT_VALIDATED" not in response
        
        return {
            "criteria": criteria,
            "is_validated": is_validated,
            "reasoning": response
        }
    
    async def _check_dependencies(self, task: Task, all_tasks: List[Task]) -> bool:
        """Check if task dependencies are satisfied."""
        if not task.dependencies:
            return True
        
        dependency_tasks = [t for t in all_tasks if t.task_id in task.dependencies]
        return all(t.status == TaskStatus.COMPLETED for t in dependency_tasks)
    
    def _analyze_dependencies(self, tasks: List[Task]) -> List[List[Task]]:
        """Analyze task dependencies and group by execution level."""
        levels = []
        remaining_tasks = tasks.copy()
        completed_task_ids = set()
        
        while remaining_tasks:
            current_level = []
            
            for task in remaining_tasks:
                if all(dep in completed_task_ids for dep in task.dependencies):
                    current_level.append(task)
            
            if not current_level:
                # Circular dependency or other issue
                break
            
            levels.append(current_level)
            for task in current_level:
                completed_task_ids.add(task.task_id)
                remaining_tasks.remove(task)
        
        return levels
    
    async def _decide_continuation(self, failed_task: Task, plan: ExecutionPlan, user_id: str) -> bool:
        """Decide whether to continue execution after a critical failure."""
        # Use LLM to make continuation decision
        decision_prompt = f"""
        A critical task has failed in our autonomous execution plan:
        
        Failed Task: {failed_task.description}
        Error: {failed_task.error}
        Remaining Tasks: {len([t for t in plan.tasks if t.status == TaskStatus.PLANNED])}
        
        Should we continue executing the remaining tasks, or abort the plan?
        Consider the criticality of the failed task and its impact on the overall goal.
        
        Respond with: CONTINUE or ABORT, followed by your reasoning.
        """
        
        messages = [{"role": "user", "content": decision_prompt}]
        response = await self.llm_service.call_llm(messages)
        
        should_continue = "CONTINUE" in response and "ABORT" not in response
        
        log_service_status("AUTONOMOUS", "warning", 
                         f"Continuation decision after failure: {'CONTINUE' if should_continue else 'ABORT'}")
        
        return should_continue
    
    async def _store_execution_results(self, execution_summary: Dict[str, Any], user_id: str):
        """Store execution results for future learning."""
        # Store in memory system for future reference
        document_content = f"""
        Autonomous Execution Summary:
        Plan ID: {execution_summary['plan_id']}
        Status: {execution_summary['status']}
        Tasks Completed: {execution_summary['tasks_completed']}/{execution_summary['total_tasks']}
        Execution Time: {execution_summary.get('execution_time', 0):.2f} seconds
        
        Results: {json.dumps(execution_summary['results'], indent=2)}
        """
        
        await self.memory_api.store_memory(
            user_id=user_id,
            content=document_content,
            memory_type="autonomous_execution",
            metadata={
                "plan_id": execution_summary["plan_id"],
                "goal_id": execution_summary["goal_id"],
                "execution_type": "autonomous"
            }
        )


class AutonomousAgent:
    """Main autonomous agent that coordinates planning and execution."""
    
    def __init__(self):
        self.planner = AutonomousPlanner(llm_service, EnhancedMemoryAPI())
        self.executor = AutonomousExecutor(llm_service, tool_service, EnhancedMemoryAPI())
        self.logger = get_logger(__name__)
        self.active_goals: Dict[str, Goal] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    async def process_autonomous_request(self, user_request: str, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a request that requires autonomous planning and execution."""
        try:
            # 1. Analyze request and create goal
            goal = await self._create_goal_from_request(user_request, user_id, context or {})
            
            # 2. Create execution plan
            plan = await self.planner.create_execution_plan(goal)
            
            # 3. Execute the plan
            results = await self.executor.execute_plan(plan, user_id)
            
            # 4. Generate user-friendly summary
            summary = await self._generate_execution_summary(goal, plan, results)
            
            return {
                "status": "success",
                "goal": goal.description,
                "plan_confidence": plan.confidence_score,
                "tasks_executed": len(plan.tasks),
                "execution_results": results,
                "summary": summary
            }
            
        except Exception as e:
            self.logger.error(f"Autonomous processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "fallback_response": "I encountered an issue with autonomous processing. Let me try a simpler approach."
            }
    
    async def _create_goal_from_request(self, request: str, user_id: str, context: Dict[str, Any]) -> Goal:
        """Create a goal from user request."""
        # Use LLM to analyze the request and extract goal information
        analysis_prompt = f"""
        Analyze this user request to extract a clear goal:
        
        Request: {request}
        Context: {json.dumps(context, indent=2)}
        
        Extract:
        1. Main goal/objective
        2. Success criteria
        3. Priority level (1-10)
        4. Any constraints or requirements
        
        Respond with JSON format:
        {{
            "goal": "clear goal statement",
            "success_criteria": ["criterion 1", "criterion 2"],
            "priority": 5,
            "requirements": ["requirement 1"]
        }}
        """
        
        messages = [{"role": "user", "content": analysis_prompt}]
        response = await llm_service.call_llm(messages)
        
        try:
            goal_data = json.loads(response)
        except json.JSONDecodeError:
            # Fallback to simple goal creation
            goal_data = {
                "goal": request,
                "success_criteria": ["Complete the requested task"],
                "priority": 5,
                "requirements": []
            }
        
        goal = Goal(
            goal_id=str(uuid4()),
            description=goal_data["goal"],
            user_id=user_id,
            priority=goal_data.get("priority", 5),
            success_criteria=goal_data.get("success_criteria", []),
            context=context
        )
        
        self.active_goals[goal.goal_id] = goal
        return goal
    
    async def _generate_execution_summary(self, goal: Goal, plan: ExecutionPlan, results: Dict[str, Any]) -> str:
        """Generate a user-friendly summary of the autonomous execution."""
        summary_prompt = f"""
        Generate a clear, user-friendly summary of this autonomous execution:
        
        Goal: {goal.description}
        Tasks Executed: {results.get('tasks_completed', 0)}/{results.get('total_tasks', 0)}
        Status: {results.get('status', 'unknown')}
        
        Execution Results: {json.dumps(results.get('results', []), indent=2)}
        
        Create a conversational summary that explains:
        1. What was accomplished
        2. Key findings or results
        3. Any issues encountered
        4. Next steps if applicable
        
        Keep it conversational and helpful.
        """
        
        messages = [{"role": "user", "content": summary_prompt}]
        summary = await llm_service.call_llm(messages)
        
        return summary


# Global autonomous agent instance
autonomous_agent = AutonomousAgent()


@handle_service_errors
async def process_autonomous_request(user_request: str, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function for autonomous request processing."""
    return await autonomous_agent.process_autonomous_request(user_request, user_id, context)
