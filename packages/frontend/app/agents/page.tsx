'use client';

import { Container, Stack, Title, Card, Grid, Badge, Text, Group } from '@mantine/core';
import { IconBrain, IconTrendingUp, IconTarget, IconRocket, IconShield, IconEye, IconChartLine, IconCoins, IconUsers, IconActivity } from '@tabler/icons-react';
import { Layout } from '@/components/Layout/Layout';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import '../../styles/glassmorphic.css';

// Map personality names to icons and descriptions
const getPersonalityDetails = (name: string) => {
  const personalities: Record<string, { icon: any; color: string; description: string }> = {
    'Illia Polosukhin': { icon: IconBrain, color: 'blue', description: 'AI-focused technical approach.' },
    'Brian Armstrong': { icon: IconShield, color: 'green', description: 'Regulatory-conscious institutional.' },
    'Satoshi Nakamoto': { icon: IconCoins, color: 'yellow', description: 'Diamond hands, maximum conviction.' },
    'Michael Saylor': { icon: IconRocket, color: 'orange', description: 'All-in maximalist, never sells.' },
    'Vitalik Buterin': { icon: IconChartLine, color: 'purple', description: 'Balanced technical approach.' },
    'ZachXBT': { icon: IconEye, color: 'red', description: 'Skeptical investigator.' },
    'Yat Siu': { icon: IconTrendingUp, color: 'pink', description: 'Gaming & metaverse bull.' },
    'Rune Christensen': { icon: IconTarget, color: 'cyan', description: 'DeFi architect, systematic.' },
    'CZ': { icon: IconShield, color: 'indigo', description: 'Conservative, builds slowly.' },
    'Larry Fink': { icon: IconCoins, color: 'gray', description: 'Institutional accumulator.' },
    'Jeff Yan': { icon: IconRocket, color: 'lime', description: 'High-frequency quick decisions.' },
    'Justin Sun': { icon: IconTrendingUp, color: 'violet', description: 'Marketing genius, buys hype.' },
  };
  
  return personalities[name] || { icon: IconBrain, color: 'blue', description: 'AI trader personality' };
};

export default function AgentsPage() {
  const { data: personalitiesData } = useQuery({
    queryKey: ['personalities'],
    queryFn: () => api.getPersonalities(),
  });

  const personalities = personalitiesData?.personalities || [];

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
              AI Agent Personalities
            </Title>
            <Text size="lg" c="dimmed" mb="lg">
              Each AI trader has a unique personality based on prominent crypto/tech founders.
              <br />These personalities drive trading behavior using real-time price predictions from Allora Network.
            </Text>
            <Badge 
              size="xl" 
              variant="gradient"
              gradient={{ from: 'indigo', to: 'cyan', deg: 45 }}
              leftSection={<IconUsers size={18} />}
              className="pulse"
              style={{ padding: '12px 24px' }}
            >
              {personalities.length} Unique Traders
            </Badge>
          </div>

          <Grid>
            {personalities.map((personality: any, index: number) => {
              const details = getPersonalityDetails(personality.name);
              const Icon = details.icon;
              
              return (
                <Grid.Col key={personality.name} span={{ base: 12, sm: 6, lg: 4 }}>
                  <Card 
                    className="market-card floating shimmer"
                    h="100%"
                    style={{ 
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
                      <Group justify="space-between" align="flex-start">
                        <Badge 
                          size="lg" 
                          variant="gradient"
                          gradient={{ from: details.color, to: details.color === 'blue' ? 'cyan' : 'indigo', deg: 45 }}
                          leftSection={<Icon size={16} />}
                          style={{ maxWidth: '100%' }}
                        >
                          {personality.name}
                        </Badge>
                      </Group>
                      
                      <div>
                        <Text size="md" fw={600} mb="xs" c="white">{personality.type}</Text>
                        <Text size="sm" c="white" style={{ fontStyle: 'italic', opacity: 0.8 }}>
                          "{details.description}"
                        </Text>
                        <Text size="sm" c="white" mt="xs" style={{ opacity: 0.7 }}>{personality.description}</Text>
                      </div>
                      
                      <div style={{
                        padding: '8px 12px',
                        background: 'rgba(255, 255, 255, 0.03)',
                        borderRadius: '8px',
                        border: '1px solid rgba(255, 255, 255, 0.05)'
                      }}>
                        <Stack gap="4px">
                          <Group justify="space-between">
                            <Text size="xs" c="white" style={{ opacity: 0.8 }}>Bullish Threshold</Text>
                            <Badge size="sm" variant="light" color={personality.bullish_threshold > 0 ? 'green' : 'red'} style={{ color: 'white' }}>
                              {personality.bullish_threshold > 0 ? '+' : ''}{personality.bullish_threshold}
                            </Badge>
                          </Group>
                          <Group justify="space-between">
                            <Text size="xs" c="white" style={{ opacity: 0.8 }}>Confidence</Text>
                            <Badge size="sm" variant="light" color="blue" style={{ color: 'white' }}>
                              {(personality.confidence_weight * 100).toFixed(0)}%
                            </Badge>
                          </Group>
                          <Group justify="space-between">
                            <Text size="xs" c="white" style={{ opacity: 0.8 }}>Trading Style</Text>
                            <Badge size="sm" variant="dot" color={
                              personality.action_bias === 'aggressive' ? 'red' :
                              personality.action_bias === 'cautious' ? 'blue' :
                              personality.action_bias === 'yolo' ? 'orange' :
                              personality.action_bias === 'balanced' ? 'green' :
                              personality.action_bias === 'strategic' ? 'purple' :
                              personality.action_bias === 'momentum' ? 'cyan' :
                              'gray'
                            } style={{ color: 'white' }}>
                              {personality.action_bias === 'yolo' ? 'YOLO' : 
                               personality.action_bias === 'aggressive' ? 'Aggr.' :
                               personality.action_bias === 'cautious' ? 'Caut.' :
                               personality.action_bias === 'balanced' ? 'Bal.' :
                               personality.action_bias === 'strategic' ? 'Strat.' :
                               personality.action_bias === 'momentum' ? 'Mtm.' :
                               personality.action_bias}
                            </Badge>
                          </Group>
                        </Stack>
                      </div>
                    </Stack>
                  </Card>
                </Grid.Col>
              );
            })}
          </Grid>

          <Card className="glass-card">
            <Stack gap="md">
              <Title order={4} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <IconActivity size={20} />
                How AI Trading Works
              </Title>
              <Text size="md" mb="md">
                Each trader uses <strong>Allora Network</strong> to get 8-hour price predictions for AI tokens 
                (Virtual, Aixbt, VaderAI, Sekoia). Based on the average AI token price and their personality traits, they decide:
              </Text>
              
              <Grid>
                <Grid.Col span={{ base: 12, md: 4 }}>
                  <div style={{
                    padding: '12px',
                    background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(16, 185, 129, 0.05))',
                    borderRadius: '12px',
                    border: '1px solid rgba(34, 197, 94, 0.2)',
                    textAlign: 'center'
                  }}>
                    <Text size="sm" fw={600} c="green">BUY YES</Text>
                    <Text size="xs" c="dimmed">Bullish on proposal</Text>
                  </div>
                </Grid.Col>
                <Grid.Col span={{ base: 12, md: 4 }}>
                  <div style={{
                    padding: '12px',
                    background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.05))',
                    borderRadius: '12px',
                    border: '1px solid rgba(239, 68, 68, 0.2)',
                    textAlign: 'center'
                  }}>
                    <Text size="sm" fw={600} c="red">BUY NO</Text>
                    <Text size="xs" c="dimmed">Bearish on proposal</Text>
                  </div>
                </Grid.Col>
                <Grid.Col span={{ base: 12, md: 4 }}>
                  <div style={{
                    padding: '12px',
                    background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(147, 51, 234, 0.05))',
                    borderRadius: '12px',
                    border: '1px solid rgba(168, 85, 247, 0.2)',
                    textAlign: 'center'
                  }}>
                    <Text size="sm" fw={600} c="violet">SELL</Text>
                    <Text size="xs" c="dimmed">Take profits/losses</Text>
                  </div>
                </Grid.Col>
              </Grid>
              
              <div style={{
                padding: '12px',
                background: 'rgba(255, 255, 255, 0.02)',
                borderRadius: '8px',
                border: '1px solid rgba(255, 255, 255, 0.05)'
              }}>
                <Text size="sm" c="dimmed" style={{ fontStyle: 'italic' }}>
                  <strong>Example:</strong> Michael Saylor is always bullish regardless of AI prices, 
                  while ZachXBT needs strong evidence and high confidence before making any bullish trades.
                </Text>
              </div>
            </Stack>
          </Card>
        </Stack>
      </Container>
    </Layout>
  );
}