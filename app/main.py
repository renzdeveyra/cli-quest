from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import logging
from typing import Dict, List
import uuid

from app.api import auth, challenges, users, websocket, leaderboard
from app.core.sandbox import DockerSandbox
from app.database.connection import get_database
from app.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="CLI Quest API",
    description="Backend API for CLI Quest - Interactive Command Line Learning Platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:4173"],  # SvelteKit dev/preview ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}
sandbox_sessions: Dict[str, DockerSandbox] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting CLI Quest API server...")

    # Skip database connection for now - will be implemented later
    logger.info("Skipping database connection (development mode)")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down CLI Quest API server...")

    # Clean up active sandbox sessions
    for session_id, sandbox in sandbox_sessions.items():
        try:
            await sandbox.cleanup()
            logger.info(f"Cleaned up sandbox session: {session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up sandbox {session_id}: {e}")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "cli-quest-api",
        "version": "0.1.0"
    })

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(challenges.router, prefix="/api/challenges", tags=["challenges"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["leaderboard"])

# WebSocket endpoint for terminal interaction
@app.websocket("/api/terminal/{session_id}")
async def websocket_terminal(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time terminal interaction"""
    await websocket.accept()
    active_connections[session_id] = websocket

    try:
        # Initialize sandbox for this session (disabled for development)
        # if session_id not in sandbox_sessions:
        #     sandbox = DockerSandbox(session_id)
        #     await sandbox.initialize()
        #     sandbox_sessions[session_id] = sandbox
        #     logger.info(f"Created new sandbox session: {session_id}")

        # sandbox = sandbox_sessions[session_id]

        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "output",
            "data": "Welcome to CLI Quest Terminal!\n$ "
        }))

        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "command":
                command = message["data"]
                logger.info(f"Executing command in session {session_id}: {command}")

                # Mock command execution for development
                try:
                    # Simple mock responses for testing
                    if command.strip() == "ls":
                        output = "file1.txt  file2.txt  secret.txt  README.txt"
                    elif command.strip() == "ls -la":
                        output = "total 4\ndrwxr-xr-x 2 user user 4096 Dec 20 12:00 .\ndrwxr-xr-x 3 user user 4096 Dec 20 12:00 ..\n-rw-r--r-- 1 user user   20 Dec 20 12:00 file1.txt\n-rw-r--r-- 1 user user   20 Dec 20 12:00 file2.txt\n-rw-r--r-- 1 user user   50 Dec 20 12:00 secret.txt\n-rw-r--r-- 1 user user   30 Dec 20 12:00 README.txt"
                    elif "cat secret.txt" in command:
                        output = "The flag is: CLI_QUEST_CAT_READER\nCongratulations on reading this file!"
                    elif command.strip() == "pwd":
                        output = "/workspace"
                    elif command.strip() == "whoami":
                        output = "user"
                    else:
                        output = f"bash: {command}: command not found"

                    await websocket.send_text(json.dumps({
                        "type": "output",
                        "data": output + "\n$ "
                    }))
                except Exception as e:
                    logger.error(f"Command execution error: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": f"Error: {str(e)}\n$ "
                    }))

            elif message["type"] == "resize":
                # Handle terminal resize (mock for development)
                cols = message.get("cols", 80)
                rows = message.get("rows", 24)
                logger.info(f"Terminal resized to {cols}x{rows}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        # Cleanup
        if session_id in active_connections:
            del active_connections[session_id]

        # Keep sandbox alive for a short time in case of reconnection
        # In production, implement proper session management

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )