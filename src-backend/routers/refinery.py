"""
ContextRefinery — Refinery Router

Core endpoint for the prompt refinement pipeline.
Supports both SSE streaming and synchronous invocation.
"""

from __future__ import annotations

import json
import time
import logging
import asyncio
from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models.schemas import RefineRequest, RefineResult, SSEEvent, SSEEventType, EvalScoresResponse
from models.state import RefineryState, SourceFile, AgentStepType
from services.token_counter import count_tokens
from services.persistence import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/refinery", tags=["refinery"])


@router.post("/stream")
async def stream_refine(request: RefineRequest):
    """
    Stream the prompt refinement process via Server-Sent Events (SSE).
    
    The client receives real-time updates as each agent processes:
    - agent_message: Thinking/progress updates from each agent
    - progress: Pipeline step completion events
    - result: The final refined prompt
    - eval: Evaluation scores
    - done: Pipeline complete
    """
    async def event_generator():
        from agents.graph import build_refinery_graph

        graph = build_refinery_graph()

        # Convert request files to SourceFile objects
        source_files = [
            SourceFile(
                path=f.path,
                filename=f.filename,
                language=f.language,
                content=f.content,
                token_count=count_tokens(f.content),
            )
            for f in request.files
        ]

        # Build initial state
        initial_state: RefineryState = {
            "user_goal": request.goal,
            "source_files": source_files,
            "token_budget": request.token_budget,
            "target_model": request.target_model.value,
            "intent_analysis": None,
            "retrieved_context": [],
            "refined_prompt": "",
            "eval_scores": None,
            "agent_messages": [],
            "iteration": 0,
            "status": "running",
            "error": None,
        }

        # Emit start event
        yield _format_sse(SSEEvent(
            event_type=SSEEventType.PROGRESS,
            data={"step": "start", "message": "🚀 Starting refinement pipeline..."},
            timestamp=time.time(),
        ))

        try:
            # Stream through LangGraph execution
            last_msg_count = 0

            async for state_update in graph.astream(initial_state):
                # Extract node name and state
                for node_name, node_state in state_update.items():
                    # Emit new agent messages
                    new_messages = node_state.get("agent_messages", [])
                    for msg in new_messages[last_msg_count:]:
                        yield _format_sse(SSEEvent(
                            event_type=SSEEventType.AGENT_MESSAGE,
                            data={
                                "step_type": msg.step_type.value if hasattr(msg.step_type, 'value') else str(msg.step_type),
                                "agent_name": msg.agent_name,
                                "content": msg.content,
                                "metadata": msg.metadata,
                            },
                            timestamp=msg.timestamp or time.time(),
                        ))
                    last_msg_count = len(new_messages)

                    # Emit progress for node completion
                    yield _format_sse(SSEEvent(
                        event_type=SSEEventType.PROGRESS,
                        data={"step": node_name, "message": f"Completed: {node_name}"},
                        timestamp=time.time(),
                    ))

                    # Emit eval scores if available
                    if "eval_scores" in node_state and node_state["eval_scores"] is not None:
                        scores = node_state["eval_scores"]
                        yield _format_sse(SSEEvent(
                            event_type=SSEEventType.EVAL,
                            data=asdict(scores),
                            timestamp=time.time(),
                        ))

                    # Emit result if available
                    if "refined_prompt" in node_state and node_state["refined_prompt"]:
                        prompt = node_state["refined_prompt"]
                        yield _format_sse(SSEEvent(
                            event_type=SSEEventType.RESULT,
                            data={
                                "refined_prompt": prompt,
                                "token_count": count_tokens(prompt),
                                "token_budget": request.token_budget,
                                "iteration": node_state.get("iteration", 0),
                            },
                            timestamp=time.time(),
                        ))

                # Small delay to prevent overwhelming the SSE stream
                await asyncio.sleep(0.05)

            # Final done event
            yield _format_sse(SSEEvent(
                event_type=SSEEventType.DONE,
                data={"message": "✅ Refinement complete"},
                timestamp=time.time(),
            ))

            # Persistent history log
            if hasattr(initial_state, "refined_prompt") and initial_state["refined_prompt"]:
                # We need to capture the final state from the graph
                pass # Note: in a stream, the final state is in the last chunk
                # I'll add logic to capture it in the next chunk

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            yield _format_sse(SSEEvent(
                event_type=SSEEventType.ERROR,
                data={"error": str(e)},
                timestamp=time.time(),
            ))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/invoke", response_model=RefineResult)
async def invoke_refine(request: RefineRequest):
    """
    Synchronous (non-streaming) prompt refinement.
    Runs the full pipeline and returns the final result.
    """
    from agents.graph import build_refinery_graph

    graph = build_refinery_graph()

    source_files = [
        SourceFile(
            path=f.path,
            filename=f.filename,
            language=f.language,
            content=f.content,
            token_count=count_tokens(f.content),
        )
        for f in request.files
    ]

    initial_state: RefineryState = {
        "user_goal": request.goal,
        "source_files": source_files,
        "token_budget": request.token_budget,
        "target_model": request.target_model.value,
        "intent_analysis": None,
        "retrieved_context": [],
        "refined_prompt": "",
        "eval_scores": None,
        "agent_messages": [],
        "iteration": 0,
        "status": "running",
        "error": None,
    }

    try:
        result = await graph.ainvoke(initial_state)

        scores = result.get("eval_scores")
        eval_resp = EvalScoresResponse(
            context_grounding=scores.context_grounding if scores else 0.0,
            budget_utilization=scores.budget_utilization if scores else 0.0,
            information_density=scores.information_density if scores else 0.0,
            overall_score=scores.overall_score if scores else 0.0,
            passed=scores.passed if scores else False,
        )

        # Save to persistent history
        db.add_history(
            project_id=request.project_id,
            goal=request.goal,
            refined_prompt=result.get("refined_prompt", ""),
            token_count=count_tokens(result.get("refined_prompt", "")),
            target_model=request.target_model.value,
            eval_scores=asdict(scores) if scores else {}
        )

        return RefineResult(
            refined_prompt=result.get("refined_prompt", ""),
            token_count=count_tokens(result.get("refined_prompt", "")),
            token_budget=request.token_budget,
            target_model=request.target_model.value,
            iterations=result.get("iteration", 0),
            eval_scores=eval_resp,
        )

    except Exception as e:
        logger.error(f"Invocation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Refinement failed: {str(e)}")


def _format_sse(event: SSEEvent) -> str:
    """Format an SSEEvent as a Server-Sent Event string."""
    data = json.dumps(event.model_dump(), default=str)
    return f"data: {data}\n\n"
