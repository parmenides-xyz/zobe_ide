#!/usr/bin/env python3
"""Test Allora network inference querying"""

from src.traders.allora_predictor import get_latest_inference

# Test exactly like the example
print("Testing Allora inference queries...")
print("=" * 50)

# Test topic 10 (memecoin predictions)
print("\nTopic 10 - Memecoin predictions:")
try:
    data = get_latest_inference(10, "https://allora-rpc.testnet.allora.network/")
    print(f"Latest inference: {data['network_inferences']['combined_value']}")
    print(f"Confidence intervals: {data['confidence_interval_values']}")
except Exception as e:
    print(f"Failed to get inference: {e}")

# Test topic 5 (Solana price)
print("\nTopic 5 - Solana price predictions:")
try:
    data = get_latest_inference(5, "https://allora-rpc.testnet.allora.network/")
    print(f"Latest inference: {data['network_inferences']['combined_value']}")
    print(f"Confidence intervals: {data['confidence_interval_values']}")
except Exception as e:
    print(f"Failed to get inference: {e}")