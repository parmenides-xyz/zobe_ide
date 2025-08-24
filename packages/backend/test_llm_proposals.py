#!/usr/bin/env python3
"""Test dynamic proposal generation via Claude API"""

from src.traders.proposal_agent import ProposalAgent
import json

def test_llm_generation():
    """Test generating proposals via LLM"""
    print("Testing LLM proposal generation...")
    
    # Try to generate proposals
    proposals = ProposalAgent.generate_proposals_via_llm(5)
    
    if proposals:
        print(f"\n✅ Successfully generated {len(proposals)} proposals via Claude API:\n")
        for i, p in enumerate(proposals, 1):
            print(f"{i}. {p['name']} ({p['symbol']})")
            print(f"   {p['description']}")
            print(f"   Capabilities: {', '.join(p['capabilities'])}")
            print()
    else:
        print("\n❌ Failed to generate proposals via LLM, using hardcoded fallback")
        
    # Test the main getter
    print("\nTesting get_agent_proposals()...")
    all_proposals = ProposalAgent.get_agent_proposals()
    print(f"Got {len(all_proposals)} proposals total")

if __name__ == "__main__":
    test_llm_generation()