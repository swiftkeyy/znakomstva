"""Property-based tests for matching algorithm properties."""
import pytest
from hypothesis import given, strategies as st, assume
from typing import List, Tuple


# Mutual match detection property
@given(
    user1_likes_user2=st.booleans(),
    user2_likes_user1=st.booleans(),
)
def test_mutual_match_detection_property(user1_likes_user2: bool, user2_likes_user1: bool) -> None:
    """
    Property: A match should be created if and only if both users liked each other.
    
    Correctness property:
    - ∀ user1, user2: match_exists(user1, user2) ⟺ (user1_likes_user2 ∧ user2_likes_user1)
    
    Uniqueness property:
    - ∀ user1, user2: mutual_like ⟹ exactly one match created
    """
    matches_before = []
    
    # Simulate swipes
    if user1_likes_user2:
        record_swipe(user_id=1, target_user_id=2, action="like")
    
    if user2_likes_user1:
        record_swipe(user_id=2, target_user_id=1, action="like")
    
    # Check for match
    match_created, match_count = check_and_create_match(user_id_1=1, user_id_2=2)
    
    if user1_likes_user2 and user2_likes_user1:
        # Both liked each other: match should be created
        assert match_created is True, "Expected match when both users liked each other"
        assert match_count == 1, f"Expected exactly 1 match, got {match_count}"
    else:
        # Not mutual: no match should be created
        assert match_created is False, "Expected no match when likes are not mutual"
        assert match_count == 0, f"Expected 0 matches, got {match_count}"


# Candidate sorting property
@given(
    candidates=st.lists(
        st.fixed_dictionaries({
            "user_id": st.integers(min_value=1, max_value=1000),
            "compatibility_score": st.floats(min_value=0.0, max_value=100.0),
            "distance_km": st.floats(min_value=0.1, max_value=100.0),
        }),
        min_size=2,
        max_size=20,
    )
)
def test_candidate_sorting_property(candidates: List[dict]) -> None:
    """
    Property: Candidates should be sorted by hybrid score (70% compatibility + 30% distance).
    
    Correctness property:
    - ∀ i, j: i < j ⟹ hybrid_score[i] ≥ hybrid_score[j] (descending order)
    
    Hybrid score formula:
    - hybrid_score = (compatibility_score * 0.7) + (distance_score * 0.3)
    - distance_score = max(0, 100 - (distance_km / max_distance * 100))
    """
    MAX_DISTANCE = 50  # km
    
    # Calculate hybrid scores
    candidates_with_scores = []
    for candidate in candidates:
        compat_score = candidate["compatibility_score"]
        distance = candidate["distance_km"]
        
        # Distance score: closer is better
        distance_score = max(0, 100 - (distance / MAX_DISTANCE * 100))
        
        # Hybrid score: 70% compatibility + 30% distance
        hybrid_score = (compat_score * 0.7) + (distance_score * 0.3)
        
        candidates_with_scores.append({
            **candidate,
            "hybrid_score": hybrid_score
        })
    
    # Sort candidates
    sorted_candidates = sort_candidates_by_hybrid_score(candidates_with_scores)
    
    # Verify sorting property: each element >= next element
    for i in range(len(sorted_candidates) - 1):
        current_score = sorted_candidates[i]["hybrid_score"]
        next_score = sorted_candidates[i + 1]["hybrid_score"]
        
        assert current_score >= next_score, \
            f"Sorting violation at index {i}: {current_score} < {next_score}"


# Match uniqueness property
@given(
    user1_id=st.integers(min_value=1, max_value=100),
    user2_id=st.integers(min_value=1, max_value=100),
    num_attempts=st.integers(min_value=1, max_value=5),
)
def test_match_uniqueness_property(user1_id: int, user2_id: int, num_attempts: int) -> None:
    """
    Property: Multiple mutual likes should create exactly one match (idempotency).
    
    Correctness property:
    - ∀ user1, user2, n: create_match(user1, user2) called n times ⟹ exactly 1 match exists
    """
    assume(user1_id != user2_id)  # Users can't match with themselves
    
    # Clear any existing matches
    clear_matches()
    
    # Simulate mutual likes
    record_swipe(user1_id, user2_id, "like")
    record_swipe(user2_id, user1_id, "like")
    
    # Attempt to create match multiple times
    match_ids = []
    for _ in range(num_attempts):
        match_created, match_id = create_match_if_mutual(user1_id, user2_id)
        if match_id:
            match_ids.append(match_id)
    
    # Verify exactly one unique match exists
    unique_matches = len(set(match_ids))
    total_matches = count_matches_between_users(user1_id, user2_id)
    
    assert unique_matches <= 1, f"Expected at most 1 unique match, got {unique_matches}"
    assert total_matches == 1, f"Expected exactly 1 match in database, got {total_matches}"


# Helper functions (these would be imported from actual service modules)
_swipes = {}
_matches = {}
_match_counter = 0


def record_swipe(user_id: int, target_user_id: int, action: str) -> None:
    """Record a swipe action."""
    _swipes[(user_id, target_user_id)] = action


def check_and_create_match(user_id_1: int, user_id_2: int) -> Tuple[bool, int]:
    """
    Check if both users liked each other and create match if so.
    
    Returns:
        (match_created, match_count)
    """
    user1_likes_user2 = _swipes.get((user_id_1, user_id_2)) == "like"
    user2_likes_user1 = _swipes.get((user_id_2, user_id_1)) == "like"
    
    if user1_likes_user2 and user2_likes_user1:
        # Create match
        match_key = tuple(sorted([user_id_1, user_id_2]))
        if match_key not in _matches:
            global _match_counter
            _match_counter += 1
            _matches[match_key] = _match_counter
        return True, 1
    
    return False, 0


def sort_candidates_by_hybrid_score(candidates: List[dict]) -> List[dict]:
    """Sort candidates by hybrid score in descending order."""
    return sorted(candidates, key=lambda c: c["hybrid_score"], reverse=True)


def create_match_if_mutual(user1_id: int, user2_id: int) -> Tuple[bool, int]:
    """Create match if mutual like exists. Returns (created, match_id)."""
    user1_likes_user2 = _swipes.get((user1_id, user2_id)) == "like"
    user2_likes_user1 = _swipes.get((user2_id, user1_id)) == "like"
    
    if user1_likes_user2 and user2_likes_user1:
        match_key = tuple(sorted([user1_id, user2_id]))
        if match_key not in _matches:
            global _match_counter
            _match_counter += 1
            _matches[match_key] = _match_counter
            return True, _matches[match_key]
        return False, _matches[match_key]
    
    return False, 0


def count_matches_between_users(user1_id: int, user2_id: int) -> int:
    """Count matches between two users."""
    match_key = tuple(sorted([user1_id, user2_id]))
    return 1 if match_key in _matches else 0


def clear_matches() -> None:
    """Clear all matches and swipes."""
    global _swipes, _matches, _match_counter
    _swipes = {}
    _matches = {}
    _match_counter = 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
