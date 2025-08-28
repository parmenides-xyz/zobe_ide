/**
 * API client for Kurtosis backend
 */

const API_URL = typeof window !== 'undefined' 
  ? (window.location.hostname.includes('phala.network') 
    ? `https://${window.location.hostname.replace('-3000', '-8001')}` 
    : 'http://localhost:8001')
  : process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface Market {
  market_id: number;
  title: string;
  deadline: number;
  is_graduated: boolean;
  winning_proposal?: number;
  total_volume?: number;
}

export interface Proposal {
  id: number;
  agent: string;
  address: string;
  data: {
    name: string;
    symbol: string;
    description: string;
    capabilities: string[];
    strategy: string;
  };
}

export interface TraderPersonality {
  name: string;
  type: string;
  description: string;
  action_bias: string;
  risk_tolerance: number;
  focus: string;
}

export interface SwarmStatus {
  market_id: number;
  active_traders: number;
  active_proposals: number[];
  total_trades: number;
  is_running: boolean;
  process_id?: string;
  leading_proposal?: number;
}

class KurtosisAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  // Markets
  async getMarkets(): Promise<Market[]> {
    const res = await fetch(`${this.baseUrl}/api/markets`);
    if (!res.ok) throw new Error('Failed to fetch markets');
    return res.json();
  }

  async getMarket(marketId: number): Promise<Market> {
    const res = await fetch(`${this.baseUrl}/api/markets/${marketId}`);
    if (!res.ok) throw new Error('Failed to fetch market');
    return res.json();
  }

  async createMarket(title: string, minDeposit: number = 1000, durationMinutes: number = 10) {
    const res = await fetch(`${this.baseUrl}/api/markets/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        min_deposit: minDeposit,
        duration_minutes: durationMinutes,
      }),
    });
    if (!res.ok) throw new Error('Failed to create market');
    return res.json();
  }

  // Swarm
  async launchSwarm(marketId?: number, numTraders: number = 20, numProposalAgents: number = 10) {
    const res = await fetch(`${this.baseUrl}/api/swarm/launch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        market_id: marketId,
        num_traders: numTraders,
        num_proposal_agents: numProposalAgents,
      }),
    });
    if (!res.ok) throw new Error('Failed to launch swarm');
    return res.json();
  }

  async getSwarmStatus(marketId: number): Promise<SwarmStatus> {
    const res = await fetch(`${this.baseUrl}/api/swarm/status/${marketId}`);
    if (!res.ok) throw new Error('Failed to fetch swarm status');
    return res.json();
  }

  async stopSwarm(marketId: number) {
    const res = await fetch(`${this.baseUrl}/api/swarm/stop/${marketId}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to stop swarm');
    return res.json();
  }

  // Traders
  async getTraders(marketId: number) {
    const res = await fetch(`${this.baseUrl}/api/traders/${marketId}`);
    if (!res.ok) throw new Error('Failed to fetch traders');
    return res.json();
  }

  async getPersonalities(): Promise<{ personalities: TraderPersonality[] }> {
    const res = await fetch(`${this.baseUrl}/api/personalities`);
    if (!res.ok) throw new Error('Failed to fetch personalities');
    return res.json();
  }

}

export const api = new KurtosisAPI();
export default api;