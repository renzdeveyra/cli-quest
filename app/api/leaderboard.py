from fastapi import APIRouter
from typing import Dict, Any, List

router = APIRouter()

@router.get("/")
async def get_leaderboard() -> List[Dict[str, Any]]:
    """Get the current leaderboard"""
    # Sample leaderboard data
    return [
        {"rank": 1, "username": "cli_master", "score": 1500, "challenges_completed": 15},
        {"rank": 2, "username": "terminal_ninja", "score": 1200, "challenges_completed": 12},
        {"rank": 3, "username": "bash_wizard", "score": 900, "challenges_completed": 9}
    ]

@router.get("/user/{user_id}")
async def get_user_rank(user_id: str) -> Dict[str, Any]:
    """Get a specific user's rank and stats"""
    return {"message": "User rank endpoint - to be implemented"}