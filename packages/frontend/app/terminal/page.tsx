'use client';

import { useState, useEffect, useRef } from 'react';
import { Container, Stack, Text, Grid, Card, Group, Badge, Button, Progress, Box } from '@mantine/core';
import { Layout } from '@/components/Layout/Layout';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { wsManager } from '@/lib/websocket';
import { IconTerminal2, IconRocket, IconActivity, IconDroplet, IconChartBar, IconPlus } from '@tabler/icons-react';
import '../../styles/terminal.css';

// ASCII Art for KURTOSIS
const ASCII_LOGO = `
██╗  ██╗██╗   ██╗██████╗ ████████╗ ██████╗ ███████╗██╗███████╗
██║ ██╔╝██║   ██║██╔══██╗╚══██╔══╝██╔═══██╗██╔════╝██║██╔════╝
█████╔╝ ██║   ██║██████╔╝   ██║   ██║   ██║███████╗██║███████╗
██╔═██╗ ██║   ██║██╔══██╗   ██║   ██║   ██║╚════██║██║╚════██║
██║  ██╗╚██████╔╝██║  ██║   ██║   ╚██████╔╝███████║██║███████║
╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚══════╝╚═╝╚══════╝`;

export default function TerminalPage() {
  const queryClient = useQueryClient();
  const [terminalLogs, setTerminalLogs] = useState<string[]>([]);
  const [selectedMarket, setSelectedMarket] = useState<number | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);
  
  // Dynamic pool state for animations
  const [poolState, setPoolState] = useState({
    yesPool: { vusd: 333.33, yes: 333.33 },
    noPool: { vusd: 333.33, no: 333.33 }
  });
  
  const { data: markets } = useQuery({
    queryKey: ['markets'],
    queryFn: () => api.getMarkets(),
    refetchInterval: false, // Use WebSocket instead
  });

  const { data: personalities } = useQuery({
    queryKey: ['personalities'],
    queryFn: () => api.getPersonalities(),
  });

  const activeMarket = markets?.find(m => !m.is_graduated) || markets?.[0];
  const marketId = activeMarket?.market_id;

  const { data: swarmStatus } = useQuery({
    queryKey: ['swarm-status', marketId],
    queryFn: () => marketId ? api.getSwarmStatus(marketId) : null,
    refetchInterval: false, // Use WebSocket instead
    enabled: !!marketId,
  });

  // Initialize terminal logs
  useEffect(() => {
    const logs = [
      '[SYSTEM] kurtosis-terminal v3.1.4',
      '[SYSTEM] Connected to Sei Network (atlantic-2)',
      '[SYSTEM] Swarm Status: STANDBY | Network: ONLINE',
      '',
    ];
    setTerminalLogs(logs);
  }, []);

  // Animate pools when swarm is active
  useEffect(() => {
    if (!swarmStatus?.is_running) return;
    
    const interval = setInterval(() => {
      setPoolState(prev => {
        // Simulate trading activity with random swaps
        const isYesPool = Math.random() > 0.5;
        const isBuying = Math.random() > 0.5; // 50% chance to buy or sell
        const tradeSize = Math.random() * 20 + 5; // 5-25 token trades
        
        if (isYesPool) {
          const k = prev.yesPool.vusd * prev.yesPool.yes; // constant product
          
          if (isBuying) {
            // Buying YES tokens (vUSD in, YES out)
            const newVusd = prev.yesPool.vusd + tradeSize;
            const newYes = k / newVusd;
            return {
              ...prev,
              yesPool: { vusd: newVusd, yes: newYes }
            };
          } else {
            // Selling YES tokens (YES in, vUSD out)
            const newYes = prev.yesPool.yes + tradeSize;
            const newVusd = k / newYes;
            return {
              ...prev,
              yesPool: { vusd: newVusd, yes: newYes }
            };
          }
        } else {
          const k = prev.noPool.vusd * prev.noPool.no;
          
          if (isBuying) {
            // Buying NO tokens (vUSD in, NO out)
            const newVusd = prev.noPool.vusd + tradeSize;
            const newNo = k / newVusd;
            return {
              ...prev,
              noPool: { vusd: newVusd, no: newNo }
            };
          } else {
            // Selling NO tokens (NO in, vUSD out)
            const newNo = prev.noPool.no + tradeSize;
            const newVusd = k / newNo;
            return {
              ...prev,
              noPool: { vusd: newVusd, no: newNo }
            };
          }
        }
      });
    }, 2000); // Update every 2 seconds
    
    return () => clearInterval(interval);
  }, [swarmStatus?.is_running]);

  // Setup WebSocket for real-time updates using singleton manager
  useEffect(() => {
    const unsubscribe = wsManager.subscribe((data) => {
      console.log('Terminal received WebSocket data:', data);
      
      // Handle market updates
      if (data.type === 'market_update') {
        queryClient.invalidateQueries({ queryKey: ['markets'] });
        if (data.market_id === marketId) {
          queryClient.invalidateQueries({ queryKey: ['swarm-status', marketId] });
        }
      }
      
      // Handle all log types - display raw message from backend
      if (data.type === 'swarm_log' || data.type === 'swarm_launch' || data.type === 'market_creation' || 
          data.type === 'proposal_created' || data.type === 'trade_executed') {
        const timestamp = new Date().toLocaleTimeString();
        if (data.message) {
          setTerminalLogs(prev => [...prev.slice(-100), `[${timestamp}] ${data.message}`]);
        }
      }
      
      // Handle swarm status changes
      if (data.type === 'swarm_launch') {
        if (data.status === 'completed' || data.status === 'error') {
          queryClient.invalidateQueries({ queryKey: ['swarm-status', marketId] });
        }
      }
      
      // Handle market creation
      if (data.type === 'market_creation') {
        if (data.status === 'completed' && data.market_id) {
          queryClient.invalidateQueries({ queryKey: ['markets'] });
          setTerminalLogs(prev => [...prev, `[SYSTEM] Market ${data.market_id} created successfully!`]);
        }
      }
    });

    return () => {
      unsubscribe();
    };
  }, [queryClient, marketId]);

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalLogs]);

  const handleLaunchSwarm = async () => {
    const timestamp = new Date().toLocaleTimeString();
    
    if (!marketId) {
      setTerminalLogs(prev => [...prev, `[${timestamp}] [ERROR] No market exists. Create a market first before launching swarm.`]);
      return;
    }
    
    setTerminalLogs(prev => [...prev, `[${timestamp}] Launching AI agent swarm...`]);
    
    try {
      await api.launchSwarm(marketId, 20, 10);
      queryClient.invalidateQueries({ queryKey: ['swarm-status', marketId] });
    } catch (error) {
      console.error('Failed to launch swarm:', error);
      setTerminalLogs(prev => [...prev, `[${timestamp}] [ERROR] Failed to launch swarm`]);
    }
  };
  
  const handleCreateMarket = async () => {
    const timestamp = new Date().toLocaleTimeString();
    setTerminalLogs(prev => [...prev, `[${timestamp}] Creating new AI Agent Launch Market...`]);
    
    try {
      await api.createMarket('AI Agent Launch Market', 1000, 10);
      setTerminalLogs(prev => [...prev, `[${timestamp}] Market creation initiated...`]);
    } catch (error) {
      console.error('Failed to create market:', error);
      setTerminalLogs(prev => [...prev, `[${timestamp}] Error: Failed to create market`]);
    }
  };

  // Get top 4 personalities for display
  const topPersonalities = personalities?.personalities ? personalities.personalities.slice(0, 4) : [];

  return (
    <Layout>
      <div className="terminal-bg" />
      <Container size="xl" p="md">
        <Stack gap="lg">
          {/* Terminal Header */}
          <Card className="terminal-card">
            <Stack gap="md">
              <Group justify="space-between">
                <Group gap="xs">
                  <div className="terminal-indicator online" />
                  <Text size="xs" className="terminal-text">kurtosis-terminal</Text>
                </Group>
                <Badge className="terminal-badge online">
                  TESTNET (ATLANTIC-2)
                </Badge>
              </Group>
              
              {/* ASCII Logo */}
              <pre className="ascii-logo">
                {ASCII_LOGO}
              </pre>
              
              <div className="system-info">
                {terminalLogs.slice(0, 5).map((log, i) => (
                  <Text key={i} size="xs" className="terminal-system-text">
                    {log}
                  </Text>
                ))}
              </div>
            </Stack>
          </Card>

          <Grid>
            {/* AI Agents Panel - Using real personalities */}
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card className="terminal-card">
                <Stack gap="sm">
                  <Group justify="space-between">
                    <Text className="terminal-header">
                      <IconActivity size={16} /> AI_AGENTS
                    </Text>
                    <Badge className="terminal-badge" style={{
                      background: swarmStatus?.is_running ? 'rgba(0, 255, 0, 0.1)' : 'rgba(255, 0, 0, 0.1)',
                      borderColor: swarmStatus?.is_running ? 'rgba(0, 255, 0, 0.5)' : 'rgba(255, 0, 0, 0.5)',
                      color: swarmStatus?.is_running ? '#00ff00' : '#ff0000'
                    }}>
                      {swarmStatus?.is_running ? 'ACTIVE' : 'STANDBY'}
                    </Badge>
                  </Group>
                  
                  <Stack gap="sm">
                    {topPersonalities.map((personality) => (
                      <Box key={personality.name} style={{ paddingBottom: '8px' }}>
                        <Group gap="xs" mb={2}>
                          <div className={`terminal-indicator ${swarmStatus?.is_running ? 'active' : ''}`} />
                          <Text size="sm" className="terminal-text">{personality.name}</Text>
                        </Group>
                        <Group gap="xl" style={{ paddingLeft: '20px' }}>
                          <Text size="xs" className={personality.risk_tolerance > 70 ? 'terminal-value positive' : 'terminal-value negative'}>
                            {personality.risk_tolerance > 70 ? 'BULLISH' : 'BEARISH'}
                          </Text>
                          <Text size="xs" className="terminal-dim">
                            Focus: {personality.focus}
                          </Text>
                        </Group>
                      </Box>
                    ))}
                  </Stack>
                </Stack>
              </Card>
            </Grid.Col>

            {/* AMM Pool Visualization - Replacing Order Book */}
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card className="terminal-card">
                <Stack gap="sm">
                  <Text className="terminal-header">
                    <IconDroplet size={16} /> AMM_POOLS
                  </Text>
                  
                  <Stack gap="md">
                    {/* YES Pool */}
                    <div>
                      <Group justify="space-between" mb="xs">
                        <Text size="xs" className="terminal-dim">YES_POOL</Text>
                        <Text size="xs" className="terminal-value positive">
                          {poolState.yesPool.vusd.toFixed(2)} vUSD / {poolState.yesPool.yes.toFixed(2)} YES
                        </Text>
                      </Group>
                      <Progress 
                        value={(poolState.yesPool.vusd / (poolState.yesPool.vusd + poolState.yesPool.yes)) * 100} 
                        color="green" 
                        size="sm"
                        className="terminal-progress"
                        style={{ transition: 'all 0.5s ease' }}
                      />
                      <Text size="xs" className="terminal-dim" mt={4}>
                        Price: {(poolState.yesPool.vusd / poolState.yesPool.yes).toFixed(4)} vUSD/YES
                      </Text>
                    </div>

                    {/* NO Pool */}
                    <div>
                      <Group justify="space-between" mb="xs">
                        <Text size="xs" className="terminal-dim">NO_POOL</Text>
                        <Text size="xs" className="terminal-value negative">
                          {poolState.noPool.vusd.toFixed(2)} vUSD / {poolState.noPool.no.toFixed(2)} NO
                        </Text>
                      </Group>
                      <Progress 
                        value={(poolState.noPool.vusd / (poolState.noPool.vusd + poolState.noPool.no)) * 100} 
                        color="red" 
                        size="sm"
                        className="terminal-progress"
                        style={{ transition: 'all 0.5s ease' }}
                      />
                      <Text size="xs" className="terminal-dim" mt={4}>
                        Price: {(poolState.noPool.vusd / poolState.noPool.no).toFixed(4)} vUSD/NO
                      </Text>
                    </div>

                    {/* Liquidity Info */}
                    <div style={{
                      padding: '8px',
                      background: 'rgba(102, 126, 234, 0.1)',
                      border: '1px solid rgba(102, 126, 234, 0.3)',
                      borderRadius: '4px'
                    }}>
                      <Text size="xs" className="terminal-header" style={{ fontSize: '10px' }}>
                        TOTAL LIQUIDITY
                      </Text>
                      <Text size="sm" className="terminal-value" style={{ color: '#667eea' }}>
                        {(poolState.yesPool.vusd + poolState.noPool.vusd).toFixed(2)} vUSD
                      </Text>
                    </div>
                  </Stack>
                </Stack>
              </Card>
            </Grid.Col>

            {/* Market Stats - Using real data */}
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card className="terminal-card">
                <Stack gap="sm">
                  <Text className="terminal-header">
                    <IconChartBar size={16} /> MARKET_STATS
                  </Text>
                  
                  <Stack gap="xs">
                    <Group justify="space-between">
                      <Text size="xs" className="terminal-dim">MARKET_ID</Text>
                      <Text size="sm" className="terminal-value">
                        {activeMarket?.market_id || 'N/A'}
                      </Text>
                    </Group>
                    
                    <Group justify="space-between">
                      <Text size="xs" className="terminal-dim">STATUS</Text>
                      <Text size="sm" className={`terminal-value ${activeMarket?.is_graduated ? 'positive' : ''}`}>
                        {activeMarket?.is_graduated ? 'GRADUATED' : 'ACTIVE'}
                      </Text>
                    </Group>
                    
                    <Group justify="space-between">
                      <Text size="xs" className="terminal-dim">PROPOSALS</Text>
                      <Text size="sm" className="terminal-value">
                        {swarmStatus?.active_proposals?.length || 0}
                      </Text>
                    </Group>
                    
                    <Group justify="space-between">
                      <Text size="xs" className="terminal-dim">TRADERS</Text>
                      <Text size="sm" className="terminal-value">
                        {swarmStatus?.active_traders || 0}
                      </Text>
                    </Group>
                    
                    <Group justify="space-between">
                      <Text size="xs" className="terminal-dim">DEADLINE</Text>
                      <Text size="sm" className="terminal-value">
                        {activeMarket?.deadline 
                          ? new Date(activeMarket.deadline * 1000).toLocaleDateString()
                          : 'N/A'}
                      </Text>
                    </Group>
                    
                    <Group justify="space-between">
                      <Text size="xs" className="terminal-dim">LEADING</Text>
                      <Text size="sm" className="terminal-value">
                        {swarmStatus?.leading_proposal ? 
                          `Prop #${swarmStatus.leading_proposal}` : 
                          swarmStatus?.total_trades ? 
                            `${swarmStatus.total_trades} trades` : 
                            'No leader yet'}
                      </Text>
                    </Group>
                  </Stack>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>

          {/* Terminal Log */}
          <Card className="terminal-card">
            <Stack gap="sm">
              <Group justify="space-between">
                <Text className="terminal-header">
                  <IconTerminal2 size={16} /> TERMINAL_LOG
                </Text>
                <Button
                  size="xs"
                  variant="subtle"
                  className="terminal-button"
                  onClick={() => setTerminalLogs([])}
                >
                  Clear
                </Button>
              </Group>
              
              <div 
                ref={terminalRef}
                className="terminal-log"
                style={{ 
                  height: '200px', 
                  overflowY: 'auto',
                  fontFamily: 'JetBrains Mono, monospace',
                }}
              >
                {terminalLogs.map((log, i) => (
                  <Text 
                    key={i} 
                    size="xs" 
                    className="terminal-log-text"
                    style={{ 
                      color: log.includes('[ERROR]') ? '#ff4444' : undefined 
                    }}
                  >
                    {log}
                  </Text>
                ))}
                <div className="terminal-cursor" />
              </div>
            </Stack>
          </Card>

          {/* Launch Buttons */}
          <Group justify="center" gap="md">
            <Button
              size="lg"
              className="terminal-launch-button"
              leftSection={<IconPlus size={20} />}
              onClick={handleCreateMarket}
              style={{
                background: 'linear-gradient(135deg, #764ba2, #667eea)',
                border: 'none'
              }}
            >
              CREATE_MARKET
            </Button>
            <Button
              size="lg"
              className="terminal-launch-button"
              leftSection={<IconRocket size={20} />}
              onClick={handleLaunchSwarm}
              disabled={!marketId || swarmStatus?.is_running}
            >
              {swarmStatus?.is_running ? 'SWARM_ACTIVE' : 'LAUNCH_SWARM'}
            </Button>
          </Group>
        </Stack>
      </Container>
    </Layout>
  );
}