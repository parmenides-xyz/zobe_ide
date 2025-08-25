'use client';

import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Group, Loader, Stack, Text, Title, Card, Badge, Grid, Button, Container } from '@mantine/core';
import { IconPlus, IconRocket, IconClock, IconTrendingUp } from '@tabler/icons-react';
import { api } from '@/lib/api';
import { formatCurrency, timeRemaining } from '@/lib/utils';
import Link from 'next/link';
import '../../styles/glassmorphic.css';

export default function ProposalList() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  
  const { data: markets, isLoading } = useQuery({
    queryKey: ['markets'],
    queryFn: () => api.getMarkets(),
    refetchInterval: false, // Use WebSocket for updates
  });

  // Setup WebSocket connection for real-time updates
  useEffect(() => {
    const websocket = api.connectWebSocket((data) => {
      console.log('ProposalList received WebSocket data:', data);
      
      // Refresh markets on any market update
      if (data.type === 'market_update' || data.type === 'market_created') {
        queryClient.invalidateQueries({ queryKey: ['markets'] });
      }
    });

    return () => {
      websocket.close();
    };
  }, [queryClient]);

  if (isLoading) {
    return (
      <Group justify="center" py="xl">
        <Loader />
      </Group>
    );
  }

  if (!markets || markets.length === 0) {
    return (
      <Card p="xl">
        <Stack align="center" gap="md">
          <Title order={3}>No Active Markets</Title>
          <Text c="dimmed">AI agent markets will appear here when created</Text>
        </Stack>
      </Card>
    );
  }
  
  const handleCreateMarket = async () => {
    setIsCreating(true);
    try {
      await api.createMarket('AI Agent Launch Market', 1000, 10);
      // Refetch markets after creating
      queryClient.invalidateQueries({ queryKey: ['markets'] });
    } catch (error) {
      console.error('Failed to create market:', error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <>
      <div className="animated-bg" />
      <Stack gap="xl">
        <Container size="lg">
          <Group justify="space-between" mb="xl">
            <div>
              <Title 
                order={1} 
                className="neon-text"
                style={{ 
                  fontSize: '2.5rem',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}
              >
                Kurtosis
              </Title>
              <Text size="lg" c="dimmed" mt="xs">
                Futarchy for agent/token launches.
              </Text>
            </div>
            <Group>
              <Button 
                onClick={handleCreateMarket}
                loading={isCreating}
                leftSection={<IconRocket size={18} />}
                size="lg"
                className="gradient-btn"
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none'
                }}
              >
                Launch New Market
              </Button>
              <Badge 
                size="xl" 
                variant="filled"
                className="pulse"
                style={{ 
                  background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                  padding: '12px 20px'
                }}
              >
                {markets.length} Live
              </Badge>
            </Group>
          </Group>
        </Container>

        <Grid>
          {markets.map((market, index) => (
            <Grid.Col key={market.market_id} span={{ base: 12, sm: 6, lg: 4 }}>
              <Card 
                component={Link}
                href={`/market/${market.market_id}`}
                className="market-card floating shimmer"
                style={{ 
                  cursor: 'pointer',
                  height: '100%',
                  animationDelay: `${index * 0.1}s`,
                  '--mouse-x': '50%',
                  '--mouse-y': '50%'
                } as React.CSSProperties}
                onMouseMove={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const x = ((e.clientX - rect.left) / rect.width) * 100;
                  const y = ((e.clientY - rect.top) / rect.height) * 100;
                  e.currentTarget.style.setProperty('--mouse-x', `${x}%`);
                  e.currentTarget.style.setProperty('--mouse-y', `${y}%`);
                }}
              >
                <Stack gap="md">
                  <Group justify="space-between">
                    <Badge 
                      size="lg"
                      variant="gradient"
                      gradient={{ from: market.is_graduated ? 'teal' : 'indigo', to: market.is_graduated ? 'lime' : 'cyan', deg: 45 }}
                    >
                      {market.is_graduated ? 'Graduated' : 'Active'}
                    </Badge>
                    <Badge variant="outline" color="gray" size="sm">
                      ID: {market.market_id}
                    </Badge>
                  </Group>

                  <div>
                    <Title order={3} style={{ marginBottom: '8px' }}>
                      {market.title}
                    </Title>
                    <Text size="sm" c="dimmed">
                      AI-powered prediction market
                    </Text>
                  </div>

                  <div style={{
                    padding: '8px 12px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    borderRadius: '8px',
                    border: '1px solid rgba(255, 255, 255, 0.05)'
                  }}>
                    <Group justify="space-between" mb="4px">
                      <Group gap="xs">
                        <IconClock size={16} style={{ opacity: 0.7 }} />
                        <Text size="sm" c="dimmed">Ends in</Text>
                      </Group>
                      <Text size="sm" fw={600}>
                        {timeRemaining(market.deadline)}
                      </Text>
                    </Group>

                    {market.total_volume && (
                      <Group justify="space-between">
                        <Group gap="xs">
                          <IconTrendingUp size={16} style={{ opacity: 0.7 }} />
                          <Text size="sm" c="dimmed">Volume</Text>
                        </Group>
                        <Text size="sm" fw={600}>
                          {formatCurrency(market.total_volume)}
                        </Text>
                      </Group>
                    )}
                  </div>

                  {market.winning_proposal && (
                    <Badge 
                      color="green" 
                      variant="light" 
                      fullWidth
                      size="lg"
                      style={{
                        background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.1))',
                        border: '1px solid rgba(34, 197, 94, 0.3)'
                      }}
                    >
                      🏆 Winner: Proposal #{market.winning_proposal}
                    </Badge>
                  )}
                </Stack>
              </Card>
            </Grid.Col>
          ))}
        </Grid>
      </Stack>
    </>
  );
}