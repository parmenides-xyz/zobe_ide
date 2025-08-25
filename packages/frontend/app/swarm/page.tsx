'use client';

import { Container, Stack, Title, Card, Grid, Badge, Text, Group, Button, NumberInput, Alert } from '@mantine/core';
import { IconNetwork, IconRocket, IconInfoCircle, IconBrain, IconUsers, IconRobot, IconActivity } from '@tabler/icons-react';
import { Layout } from '@/components/Layout/Layout';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import '../../styles/glassmorphic.css';

export default function SwarmPage() {
  const queryClient = useQueryClient();
  const [numTraders, setNumTraders] = useState(20);
  const [numProposals, setNumProposals] = useState(10);
  const [swarmLogs, setSwarmLogs] = useState<string[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const { data: markets } = useQuery({
    queryKey: ['markets'],
    queryFn: () => api.getMarkets(),
    refetchInterval: false, // Use WebSocket instead
  });

  const activeMarket = markets?.find(m => !m.is_graduated);
  const marketId = activeMarket?.market_id;

  const { data: swarmStatus } = useQuery({
    queryKey: ['swarm-status', marketId],
    queryFn: () => marketId ? api.getSwarmStatus(marketId) : null,
    refetchInterval: false, // Use WebSocket instead
    enabled: !!marketId,
  });

  useEffect(() => {
    const websocket = api.connectWebSocket((data) => {
      console.log('Swarm page received WebSocket data:', data);
      
      // Handle market updates
      if (data.type === 'market_update') {
        queryClient.invalidateQueries({ queryKey: ['markets'] });
        if (data.market_id === marketId) {
          queryClient.invalidateQueries({ queryKey: ['swarm-status', marketId] });
        }
      }
      
      // Handle swarm logs
      if (data.type === 'swarm_log' || data.type === 'swarm_launch') {
        if (data.message) {
          setSwarmLogs(prev => [...prev.slice(-100), `[${new Date().toLocaleTimeString()}] ${data.message}`]);
        }
      }
      
      // Handle swarm status changes
      if (data.type === 'swarm_launch') {
        if (data.status === 'completed' || data.status === 'error') {
          queryClient.invalidateQueries({ queryKey: ['swarm-status', marketId] });
        }
      }
    });
    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, [queryClient, marketId]);

  const handleLaunchSwarm = async () => {
    if (!marketId) return;
    
    try {
      setSwarmLogs([`Launching swarm with ${numTraders} traders and ${numProposals} proposal agents...`]);
      await api.launchSwarm(marketId, numTraders, numProposals);
      queryClient.invalidateQueries({ queryKey: ['swarm-status', marketId] });
    } catch (error) {
      console.error('Failed to launch swarm:', error);
      setSwarmLogs(prev => [...prev, `Error: Failed to launch swarm - ${error}`]);
    }
  };

  const handleStopSwarm = async () => {
    if (!marketId) return;
    
    try {
      await api.stopSwarm(marketId);
      queryClient.invalidateQueries({ queryKey: ['swarm-status', marketId] });
      setSwarmLogs(prev => [...prev, 'Swarm stopped successfully']);
    } catch (error) {
      console.error('Failed to stop swarm:', error);
      setSwarmLogs(prev => [...prev, `Error: Failed to stop swarm - ${error}`]);
    }
  };

  return (
    <Layout>
      <div className="animated-bg" />
      <Container size="xl" p="md">
        <Stack gap="xl">
          <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
            <Title 
              order={1}
              className="neon-text"
              style={{ 
                fontSize: '2.5rem',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                marginBottom: '1rem'
              }}
            >
              🤖 AI Swarm Control Center
            </Title>
            <Text size="lg" c="dimmed" mb="lg">
              Launch and manage autonomous AI trading agents
            </Text>
            <Badge 
              size="xl" 
              variant="gradient"
              gradient={{ from: swarmStatus?.is_running ? 'teal' : 'gray', to: swarmStatus?.is_running ? 'lime' : 'gray', deg: 45 }}
              leftSection={<IconNetwork size={18} />}
              className={swarmStatus?.is_running ? 'pulse' : ''}
              style={{ padding: '12px 24px' }}
            >
              {swarmStatus?.is_running ? 'Swarm Active' : 'Swarm Inactive'}
            </Badge>
          </div>

          {!activeMarket && (
            <Alert 
              icon={<IconInfoCircle size={16} />} 
              color="blue"
              className="glass-card"
              style={{
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05))',
                border: '1px solid rgba(59, 130, 246, 0.2)'
              }}
            >
              No active markets found. Please create a market first to launch a swarm.
            </Alert>
          )}

          {activeMarket && (
            <Grid>
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card className="glass-card">
                  <Stack gap="md">
                    <Title order={4} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <IconRobot size={20} />
                      Current Market
                    </Title>
                    <Stack gap="xs">
                      <Group justify="space-between">
                        <Text size="sm" c="dimmed">Market ID</Text>
                        <Badge>#{activeMarket.market_id}</Badge>
                      </Group>
                      <Group justify="space-between">
                        <Text size="sm" c="dimmed">Title</Text>
                        <Text size="sm">{activeMarket.title}</Text>
                      </Group>
                      <Group justify="space-between">
                        <Text size="sm" c="dimmed">Status</Text>
                        <Badge color={activeMarket.is_graduated ? 'green' : 'blue'}>
                          {activeMarket.is_graduated ? 'Graduated' : 'Active'}
                        </Badge>
                      </Group>
                    </Stack>
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card className="glow-card">
                  <Stack gap="md">
                    <Title order={4} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <IconBrain size={20} />
                      Swarm Configuration
                    </Title>
                    
                    {swarmStatus?.is_running ? (
                      <Stack gap="sm">
                        <Group justify="space-between">
                          <Text size="sm">Active Traders:</Text>
                          <Text fw={500}>{swarmStatus.active_traders}</Text>
                        </Group>
                        <Group justify="space-between">
                          <Text size="sm">Active Proposals:</Text>
                          <Text fw={500}>{swarmStatus.active_proposals?.length || 0}</Text>
                        </Group>
                        <Group justify="space-between">
                          <Text size="sm">Total Trades:</Text>
                          <Text fw={500}>{swarmStatus.total_trades}</Text>
                        </Group>
                        {swarmStatus.process_id && (
                          <Group justify="space-between">
                            <Text size="sm">Process ID:</Text>
                            <Text size="xs" style={{ fontFamily: 'monospace' }}>
                              {swarmStatus.process_id}
                            </Text>
                          </Group>
                        )}
                        <Button
                          fullWidth
                          color="red"
                          leftSection={<IconNetwork size={16} />}
                          onClick={handleStopSwarm}
                        >
                          Stop Swarm
                        </Button>
                      </Stack>
                    ) : (
                      <Stack gap="sm">
                        <NumberInput
                          label="Number of Traders"
                          description="AI traders with diverse personalities"
                          value={numTraders}
                          onChange={(val) => setNumTraders(Number(val))}
                          min={1}
                          max={100}
                        />
                        <NumberInput
                          label="Number of Proposal Agents"
                          description="Agents that create AI proposals"
                          value={numProposals}
                          onChange={(val) => setNumProposals(Number(val))}
                          min={1}
                          max={20}
                        />
                        <Button
                          fullWidth
                          leftSection={<IconRocket size={18} />}
                          onClick={handleLaunchSwarm}
                          disabled={!activeMarket || activeMarket.is_graduated}
                          size="lg"
                          className="gradient-btn"
                          style={{
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            border: 'none'
                          }}
                        >
                          Launch AI Swarm
                        </Button>
                      </Stack>
                    )}
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          )}

          {swarmLogs.length > 0 && (
            <Card className="glass-card">
              <Stack gap="md">
                <Group justify="space-between">
                  <Title order={4} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <IconActivity size={20} />
                    Activity Log
                  </Title>
                  <Button 
                    size="xs" 
                    variant="subtle"
                    onClick={() => setSwarmLogs([])}
                  >
                    Clear
                  </Button>
                </Group>
                <Stack 
                  gap="xs" 
                  style={{ 
                    maxHeight: '400px', 
                    overflowY: 'auto',
                    backgroundColor: 'var(--mantine-color-dark-7)',
                    padding: '10px',
                    borderRadius: '4px'
                  }}
                >
                  {swarmLogs.map((log, index) => (
                    <Text 
                      key={index} 
                      size="xs" 
                      style={{ fontFamily: 'monospace' }}
                      c={log.includes('Error') ? 'red' : 'dimmed'}
                    >
                      {log}
                    </Text>
                  ))}
                </Stack>
              </Stack>
            </Card>
          )}

          <Card className="glass-card">
            <Stack gap="md">
              <Title order={4} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <IconUsers size={20} />
                How the AI Swarm Works
              </Title>
              <Stack gap="md">
                <div style={{
                  padding: '12px',
                  background: 'rgba(255, 255, 255, 0.03)',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.05)'
                }}>
                  <Text size="sm" mb="xs">
                    <strong>1. Proposal Creation:</strong> AI agents generate proposals for novel agent/token pairs.
                  </Text>
                </div>
                <div style={{
                  padding: '12px',
                  background: 'rgba(255, 255, 255, 0.03)',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.05)'
                }}>
                  <Text size="sm" mb="xs">
                    <strong>2. Trading Activity:</strong> Agentic traders analyze and trade YES/NO tokens.
                  </Text>
                </div>
                <div style={{
                  padding: '12px',
                  background: 'rgba(255, 255, 255, 0.03)',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.05)'
                }}>
                  <Text size="sm" mb="xs">
                    <strong>3. Market Graduation:</strong> Highest YES price proposal wins when the deadline expires.
                  </Text>
                </div>
                <div style={{
                  padding: '12px',
                  background: 'rgba(255, 255, 255, 0.03)',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.05)'
                }}>
                  <Text size="sm">
                    <strong>4. Token Launch:</strong> Winner deploys as a live AI agent token with a DragonSwap pair.
                  </Text>
                </div>
              </Stack>
            </Stack>
          </Card>
        </Stack>
      </Container>
    </Layout>
  );
}