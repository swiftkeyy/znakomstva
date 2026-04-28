"""Property-based tests for balance and transaction properties."""
import pytest
from hypothesis import given, strategies as st
from typing import Dict, Any


# Crystal deduction property
@given(
    initial_balance=st.integers(min_value=0, max_value=10000),
    deduction_amount=st.integers(min_value=1, max_value=1000),
)
def test_crystal_deduction_property(initial_balance: int, deduction_amount: int) -> None:
    """
    Property: Crystal deduction should succeed if balance is sufficient, fail otherwise.
    Balance should remain unchanged on failure.
    
    Correctness properties:
    1. ∀ balance, amount: balance ≥ amount ⟹ deduct(balance, amount) = (True, balance - amount)
    2. ∀ balance, amount: balance < amount ⟹ deduct(balance, amount) = (False, balance)
    
    Invariant: Balance never goes negative
    """
    success, new_balance = deduct_crystals(initial_balance, deduction_amount)
    
    if initial_balance >= deduction_amount:
        # Sufficient balance: deduction should succeed
        assert success is True, f"Expected success with balance {initial_balance} ≥ amount {deduction_amount}"
        assert new_balance == initial_balance - deduction_amount, \
            f"Expected balance {initial_balance - deduction_amount}, got {new_balance}"
    else:
        # Insufficient balance: deduction should fail, balance unchanged
        assert success is False, f"Expected failure with balance {initial_balance} < amount {deduction_amount}"
        assert new_balance == initial_balance, \
            f"Expected unchanged balance {initial_balance}, got {new_balance}"
    
    # Invariant: balance never negative
    assert new_balance >= 0, f"Balance went negative: {new_balance}"


# Profile update confirmation property
@given(
    profile_data=st.fixed_dictionaries({
        "age": st.integers(min_value=18, max_value=100),
        "city": st.text(min_size=1, max_size=50),
        "about_me": st.text(min_size=0, max_size=500),
    }),
    user_confirmed=st.booleans(),
)
def test_profile_update_confirmation_property(profile_data: Dict[str, Any], user_confirmed: bool) -> None:
    """
    Property: Profile should only be updated after user confirmation.
    
    Correctness property:
    - ∀ profile_data, confirmed: update_profile(profile_data, confirmed) succeeds ⟺ confirmed = True
    - ∀ profile_data: ¬confirmed ⟹ profile remains unchanged
    """
    original_profile = {"age": 25, "city": "Moscow", "about_me": "Original bio"}
    
    updated_profile, success = update_profile_with_confirmation(
        original_profile.copy(),
        profile_data,
        user_confirmed
    )
    
    if user_confirmed:
        # Profile should be updated
        assert success is True, "Expected success when user confirmed"
        assert updated_profile == profile_data, \
            f"Expected profile to be updated to {profile_data}, got {updated_profile}"
    else:
        # Profile should remain unchanged
        assert success is False, "Expected failure when user did not confirm"
        assert updated_profile == original_profile, \
            f"Expected profile to remain {original_profile}, got {updated_profile}"


# SuperSwipe cost deduction property
@given(
    crystal_balance=st.integers(min_value=0, max_value=1000),
    is_premium=st.booleans(),
)
def test_superswipe_cost_property(crystal_balance: int, is_premium: bool) -> None:
    """
    Property: SuperSwipe should deduct correct cost based on premium status.
    
    Correctness properties:
    1. Premium users: cost = 5 crystals
    2. Free users: cost = 10 crystals
    3. SuperSwipe succeeds ⟺ balance ≥ cost
    """
    PREMIUM_COST = 5
    FREE_COST = 10
    
    expected_cost = PREMIUM_COST if is_premium else FREE_COST
    
    success, new_balance, actual_cost = perform_superswipe(crystal_balance, is_premium)
    
    if crystal_balance >= expected_cost:
        # Sufficient balance
        assert success is True, f"Expected success with balance {crystal_balance} ≥ cost {expected_cost}"
        assert new_balance == crystal_balance - expected_cost, \
            f"Expected balance {crystal_balance - expected_cost}, got {new_balance}"
        assert actual_cost == expected_cost, \
            f"Expected cost {expected_cost}, got {actual_cost}"
    else:
        # Insufficient balance
        assert success is False, f"Expected failure with balance {crystal_balance} < cost {expected_cost}"
        assert new_balance == crystal_balance, \
            f"Expected unchanged balance {crystal_balance}, got {new_balance}"
        assert actual_cost == 0, f"Expected no cost deduction, got {actual_cost}"


# Helper functions (these would be imported from actual service modules)
def deduct_crystals(balance: int, amount: int) -> tuple[bool, int]:
    """
    Attempt to deduct crystals from balance.
    
    Returns:
        (success, new_balance)
    """
    if balance >= amount:
        return True, balance - amount
    return False, balance


def update_profile_with_confirmation(
    original_profile: Dict[str, Any],
    new_data: Dict[str, Any],
    confirmed: bool
) -> tuple[Dict[str, Any], bool]:
    """
    Update profile only if user confirmed.
    
    Returns:
        (updated_profile, success)
    """
    if confirmed:
        return new_data, True
    return original_profile, False


def perform_superswipe(balance: int, is_premium: bool) -> tuple[bool, int, int]:
    """
    Perform SuperSwipe action with cost deduction.
    
    Returns:
        (success, new_balance, cost_deducted)
    """
    cost = 5 if is_premium else 10
    
    if balance >= cost:
        return True, balance - cost, cost
    return False, balance, 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
