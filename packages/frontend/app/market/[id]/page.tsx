'use client';

import { useParams } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Container, Stack, Title, Card, Grid, Badge, Group, Text, Button, Loader, Progress, NumberInput } from '@mantine/core';
import { IconRocket, IconNetwork, IconClock, IconTrendingUp, IconUsers, IconBrain, IconActivity } from '@tabler/icons-react';
import { Layout } from '@/components/Layout/Layout';
import { api } from '@/lib/api';
import { formatCurrency, timeRemaining } from '@/lib/utils';
import '../../../styles/glassmorphic.css';

export default function MarketDetailPage() {
  const params = useParams();
  const marketId = Number(params.id);
  const queryClient = useQueryClient();
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [numTraders, setNumTraders] = useState(20);
  const [numProposals, setNumProposals] = useState(10);
  const [swarmLogs, setSwarmLogs] = useState<string[]>([]);

  const { data: market, isLoading } = useQuery({
    queryKey: ['market', marketId],
    queryFn: () => api.getMarket(marketId),
    refetchInterval: false, // Use WebSocket updates instead
  });

  const { data: swarmStatus } = useQuery({
    queryKey: ['swarm-status', marketId],
    queryFn: () => api.getSwarmStatus(marketId),
    refetchInterval: false, // Use WebSocket updates instead
  });

  const { data: traders } = useQuery({
    queryKey: ['traders', marketId],
    queryFn: () => api.getTraders(marketId),
    refetchInterval: false, // Use WebSocket updates instead
    enabled: !!swarmStatus?.is_running,
  });

  useEffect(() => {
    const websocket = api.connectWebSocket((data) => {
      console.log('Market page received WebSocket data:', data);
      
      // Handle market updates from WebSocket
      if (data.type === 'market_update') {
        if (data.market_id === marketId) {
          console.log('Refreshing market data for market', marketId);
          // Refresh market and swarm status when we get updates
          queryClient.invalidateQueries({ queryKey: ['market', marketId] });
          queryClient.invalidateQueries({ queryKey: ['swarm-status', marketId] });
          if (data.swarm_status?.is_running) {
            queryClient.invalidateQueries({ queryKey: ['traders', marketId] });
          }
        }
      }
      
      // Handle other events
      if (data.market_id === marketId || !data.market_id) {
        if (data.type === 'trade_executed' || data.type === 'proposal_created') {
          console.log('Trade/proposal event, refreshing data');
          queryClient.invalidateQueries({ queryKey: ['market', marketId] });
          queryClient.invalidateQueries({ queryKey: ['traders', marketId] });
        }
        if (data.type === 'swarm_log') {
          setSwarmLogs(prev => [...prev.slice(-50), data.message || 'Unknown log']);
        }
        if (data.type === 'swarm_launch') {
          // Refresh swarm status on launch events
          queryClient.invalidateQueries({ queryKey: ['swarm-status', marketId] });
          if (data.message) {
            setSwarmLogs(prev => [...prev.slice(-50), data.message]);
          }
        }
      }
    });
    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, [marketId, queryClient]);

  const handleLaunchSwarm = async () => {
    try {
      await api.launchSwarm(marketId, numTraders, numProposals);
      queryClient.invalidateQueries({ queryKey: ['swarm-status', marketId] });
    } catch (error) {
      console.error('Failed to launch swarm:', error);
    }
  };

  const handleStopSwarm = async () => {
    try {
      await api.stopSwarm(marketId);
      queryClient.invalidateQueries({ queryKey: ['swarm-status', marketId] });
    } catch (error) {
      console.error('Failed to stop swarm:', error);
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <Container p="md">
          <Group justify="center" py="xl">
            <Loader />
          </Group>
        </Container>
      </Layout>
    );
  }

  if (!market) {
    return (
      <Layout>
        <Container p="md">
          <Card p="xl">
            <Stack align="center" gap="md">
              <Title order={3}>Market Not Found</Title>
              <Text c="dimmed">Market #{marketId} does not exist</Text>
            </Stack>
          </Card>
        </Container>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="animated-bg" />
      <Container size="xl" p="md">
        <Stack gap="xl">
          <div className="glass-card" style={{ padding: '2rem', marginBottom: '1rem' }}>
            <Group justify="space-between" align="center">
              <div>
                <Title 
                  order={1}
                  style={{ 
                    fontSize: '2rem',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    marginBottom: '0.5rem'
                  }}
                >
                  {market.title}
                </Title>
                <Text size="lg" c="dimmed">
                  Market #{market.market_id} • AI Agent Prediction Market
                </Text>
              </div>
              <Badge 
                size="xl" 
                variant="gradient"
                gradient={{ from: market.is_graduated ? 'teal' : 'indigo', to: market.is_graduated ? 'lime' : 'cyan', deg: 45 }}
                className="pulse"
                style={{ padding: '12px 24px' }}
              >
                {market.is_graduated ? '🎓 Graduated' : '🚀 Active'}
              </Badge>
            </Group>
          </div>

          <Grid>
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card className="glass-card">
                <Stack gap="md">
                  <Title order={4} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <IconActivity size={20} />
                    Market Stats
                  </Title>
                  
                  <div style={{
                    padding: '12px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    borderRadius: '12px',
                    border: '1px solid rgba(255, 255, 255, 0.05)'
                  }}>
                    <Stack gap="sm">
                      <Group justify="space-between">
                        <Group gap="xs">
                          <IconClock size={16} style={{ opacity: 0.7 }} />
                          <Text size="sm" c="dimmed">Time Remaining</Text>
                        </Group>
                        <Text fw={600} className="neon-text">{timeRemaining(market.deadline)}</Text>
                      </Group>
                      <Group justify="space-between">
                        <Group gap="xs">
                          <IconTrendingUp size={16} style={{ opacity: 0.7 }} />
                          <Text size="sm" c="dimmed">Total Volume</Text>
                        </Group>
                        <Text fw={600}>{formatCurrency(market.total_volume || 0)}</Text>
                      </Group>
                      {market.winning_proposal && (
                        <Group justify="space-between">
                          <Text size="sm" c="dimmed">Winner</Text>
                          <Badge 
                            color="green" 
                            variant="light"
                            style={{
                              background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.1))',
                              border: '1px solid rgba(34, 197, 94, 0.3)'
                            }}
                          >
                            🏆 Proposal #{market.winning_proposal}
                          </Badge>
                        </Group>
                      )}
                    </Stack>
                  </div>
                </Stack>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 8 }}>
              <Card className="glow-card">
                <Stack gap="md">
                  <Title order={4} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <IconBrain size={20} />
                    AI Swarm Control
                  </Title>
                  
                  {swarmStatus?.is_running ? (
                    <Stack gap="sm">
                      <Group justify="space-between">
                        <Text size="sm">Status:</Text>
                        <Badge color="green">Running</Badge>
                      </Group>
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
                          <Text size="xs" c="dimmed">{swarmStatus.process_id}</Text>
                        </Group>
                      )}
                      <Button
                        color="red"
                        leftSection={<IconNetwork size={16} />}
                        onClick={handleStopSwarm}
                        disabled={market.is_graduated}
                      >
                        Stop Swarm
                      </Button>
                    </Stack>
                  ) : (
                    <Stack gap="sm">
                      <NumberInput
                        label="Number of Traders"
                        value={numTraders}
                        onChange={(val) => setNumTraders(Number(val))}
                        min={1}
                        max={100}
                      />
                      <NumberInput
                        label="Number of Proposal Agents"
                        value={numProposals}
                        onChange={(val) => setNumProposals(Number(val))}
                        min={1}
                        max={20}
                      />
                      <Button
                        leftSection={<IconRocket size={16} />}
                        onClick={handleLaunchSwarm}
                        disabled={market.is_graduated}
                        size="lg"
                        className="gradient-btn"
                        style={{
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          border: 'none',
                          width: '100%'
                        }}
                      >
                        🚀 Launch AI Swarm
                      </Button>
                    </Stack>
                  )}
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>

          {traders && traders.length > 0 && (
            <Card className="glass-card">
              <Stack gap="md">
                <Title order={4} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <IconUsers size={20} />
                  Active AI Traders
                </Title>
                <Grid>
                  {traders.slice(0, 12).map((trader: any, index: number) => (
                    <Grid.Col key={trader.address} span={{ base: 6, sm: 4, md: 3 }}>
                      <Card 
                        className="glass-card floating"
                        p="xs"
                        style={{ 
                          animationDelay: `${index * 0.05}s`,
                          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.03))'
                        }}
                      >
                        <Stack gap="xs">
                          <Text size="xs" c="dimmed">Trader #{index + 1}</Text>
                          <Text size="xs" style={{ fontFamily: 'monospace' }}>
                            {trader.address.slice(0, 6)}...{trader.address.slice(-4)}
                          </Text>
                          {trader.personality && (
                            <Badge size="xs" variant="light">
                              {trader.personality.name}
                            </Badge>
                          )}
                          <Text size="xs">
                            Balance: {formatCurrency(trader.balance)}
                          </Text>
                          <Text size="xs">
                            Trades: {trader.trades_executed}
                          </Text>
                        </Stack>
                      </Card>
                    </Grid.Col>
                  ))}
                </Grid>
                {traders.length > 12 && (
                  <Text size="sm" c="dimmed" ta="center">
                    And {traders.length - 12} more traders...
                  </Text>
                )}
              </Stack>
            </Card>
          )}

          {swarmLogs.length > 0 && (
            <Card className="glass-card">
              <Stack gap="md">
                <Title order={4} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <IconActivity size={20} />
                  Swarm Activity Log
                </Title>
                <Stack 
                  gap="xs" 
                  style={{ 
                    maxHeight: '200px', 
                    overflowY: 'auto',
                    padding: '12px',
                    background: 'rgba(0, 0, 0, 0.2)',
                    borderRadius: '8px',
                    border: '1px solid rgba(255, 255, 255, 0.05)'
                  }}
                >
                  {swarmLogs.map((log, index) => (
                    <Text 
                      key={index} 
                      size="xs" 
                      style={{ 
                        fontFamily: 'monospace',
                        opacity: 0.8
                      }}
                    >
                      {log}
                    </Text>
                  ))}
                </Stack>
              </Stack>
            </Card>
          )}
        </Stack>
      </Container>
    </Layout>
  );
}