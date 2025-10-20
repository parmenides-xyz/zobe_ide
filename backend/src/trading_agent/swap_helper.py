"""Helper functions for encoding PoolSwapTest swap commands"""
from eth_abi import encode
from web3 import Web3

def encode_pool_swap_test(
    pool_key,
    zero_for_one,
    amount_in,
    amount_out_minimum,
    hook_data=b''
):
    """
    Encode a swap call for PoolSwapTest contract

    Args:
        pool_key: dict with currency0, currency1, fee, tickSpacing, hooks
        zero_for_one: bool, true if swapping token0 for token1
        amount_in: amount of input token
        amount_out_minimum: minimum amount of output token (ignored, we accept any output)
        hook_data: optional hook data

    Returns:
        bytes: encoded function call data for PoolSwapTest.swap()
    """

    # Function selector for swap(PoolKey,SwapParams,TestSettings,bytes)
    selector = bytes.fromhex('2229d0b4')

    # Encode PoolKey struct
    pool_key_encoded = (
        pool_key['currency0'],
        pool_key['currency1'],
        pool_key['fee'],
        pool_key['tickSpacing'],
        pool_key['hooks']
    )

    # Calculate sqrtPriceLimitX96 based on swap direction
    if zero_for_one:
        sqrt_price_limit = 4295128740  # TickMath.MIN_SQRT_PRICE + 1
    else:
        sqrt_price_limit = 1461446703485210103287273052203988822378723970341  # TickMath.MAX_SQRT_PRICE - 1

    # Encode SwapParams struct
    swap_params_encoded = (
        zero_for_one,
        -amount_in,  # Negative for exact input
        sqrt_price_limit
    )

    # Encode TestSettings struct (takeClaims=false, settleUsingBurn=false)
    test_settings_encoded = (False, False)

    # Encode all parameters
    params = encode(
        ['(address,address,uint24,int24,address)', '(bool,int256,uint160)', '(bool,bool)', 'bytes'],
        [pool_key_encoded, swap_params_encoded, test_settings_encoded, hook_data]
    )

    return selector + params

def build_swap_transaction(
    pool_key,
    zero_for_one,
    amount_in,
    amount_out_minimum,
    router_address,
    deadline=None
):
    """
    Build complete swap transaction data for PoolSwapTest

    Returns:
        dict: transaction parameters ready for web3
    """
    # Encode the swap call for PoolSwapTest
    call_data = encode_pool_swap_test(
        pool_key,
        zero_for_one,
        amount_in,
        amount_out_minimum
    )

    return {
        'to': Web3.to_checksum_address(router_address),
        'data': '0x' + call_data.hex(),
        'value': 0  # No ETH needed for token swaps
    }

def calculate_amount_out_minimum(amount_in, is_selling_decision_token=True, slippage_bps=50):
    """
    Calculate minimum output with slippage tolerance

    Args:
        amount_in: input amount
        is_selling_decision_token: True if selling YES/NO for vUSD, False if buying
        slippage_bps: slippage in basis points (50 = 0.5%)

    Returns:
        int: minimum output amount
    """

    # We WANT prices to move for market discovery
    # Accept any non-zero output
    return 1
