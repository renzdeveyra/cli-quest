from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import uuid

router = APIRouter()

# Temporary in-memory storage for challenges
# In production, this would come from the database
SAMPLE_CHALLENGES = [
    {
        "id": "basic-ls",
        "title": "List Files",
        "description": "Learn to list files and directories using the ls command",
        "difficulty": "beginner",
        "category": "file-operations",
        "instructions": "Use the 'ls' command to list all files in the current directory. Then use 'ls -la' to see detailed information.",
        "expected_commands": ["ls", "ls -la"],
        "flag": "CLI_QUEST_LS_MASTER",
        "setup_files": {
            "file1.txt": "This is file 1",
            "file2.txt": "This is file 2",
            "hidden_file.txt": "This is a hidden file"
        }
    },
    {
        "id": "basic-cat",
        "title": "Read File Contents",
        "description": "Learn to read file contents using the cat command",
        "difficulty": "beginner",
        "category": "file-operations",
        "instructions": "Use the 'cat' command to read the contents of secret.txt. The flag is hidden inside!",
        "expected_commands": ["cat secret.txt"],
        "flag": "CLI_QUEST_CAT_READER",
        "setup_files": {
            "secret.txt": "The flag is: CLI_QUEST_CAT_READER\nCongratulations on reading this file!",
            "readme.txt": "Try reading different files to find the flag!"
        }
    }
]


@router.get("/")
async def get_challenges() -> List[Dict[str, Any]]:
    """Get all available challenges"""
    return [
        {
            "id": challenge["id"],
            "title": challenge["title"],
            "description": challenge["description"],
            "difficulty": challenge["difficulty"],
            "category": challenge["category"]
        }
        for challenge in SAMPLE_CHALLENGES
    ]


@router.get("/{challenge_id}")
async def get_challenge(challenge_id: str) -> Dict[str, Any]:
    """Get a specific challenge by ID"""
    challenge = next((c for c in SAMPLE_CHALLENGES if c["id"] == challenge_id), None)

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Don't expose the flag in the response
    response = challenge.copy()
    response.pop("flag", None)

    return response


@router.post("/{challenge_id}/start")
async def start_challenge(challenge_id: str) -> Dict[str, Any]:
    """Start a challenge session"""
    challenge = next((c for c in SAMPLE_CHALLENGES if c["id"] == challenge_id), None)

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Generate a session ID for this challenge attempt
    session_id = str(uuid.uuid4())

    return {
        "session_id": session_id,
        "challenge_id": challenge_id,
        "websocket_url": f"/api/terminal/{session_id}",
        "setup_files": challenge.get("setup_files", {})
    }


@router.post("/{challenge_id}/submit")
async def submit_flag(challenge_id: str, submission: Dict[str, str]) -> Dict[str, Any]:
    """Submit a flag for verification"""
    challenge = next((c for c in SAMPLE_CHALLENGES if c["id"] == challenge_id), None)

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    submitted_flag = submission.get("flag", "").strip()
    expected_flag = challenge["flag"]

    if submitted_flag == expected_flag:
        return {
            "success": True,
            "message": "Congratulations! You've completed the challenge!",
            "points": 100  # Basic scoring
        }
    else:
        return {
            "success": False,
            "message": "Incorrect flag. Keep trying!",
            "points": 0
        }