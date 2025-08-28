'use client';

import { Container, Stack, Title, Text, Card, Grid, Badge } from '@mantine/core';
import { Layout } from '@/components/Layout/Layout';
import { IconBrain, IconNetwork, IconChartLine, IconActivity } from '@tabler/icons-react';
import Link from 'next/link';

export default function HomePage() {
  return (
    <Layout>
      <Container size="xl" p="md">
        <Stack gap="xl">
          <Card style={{ padding: '2rem', textAlign: 'center', background: 'rgba(13, 13, 20, 0.9)', border: '1px solid rgba(102, 126, 234, 0.3)' }}>
            <Title order={1} style={{ color: 'white', marginBottom: '1rem' }}>
              Kurtosis Terminal
            </Title>
            <Text size="lg" c="white" mb="lg">
              AI-powered prediction markets on Sei blockchain
            </Text>
            <Link href="/terminal" style={{ textDecoration: 'none' }}>
              <Badge 
                size="xl" 
                style={{ 
                  padding: '12px 24px',
                  background: 'linear-gradient(135deg, #667eea, #764ba2)',
                  cursor: 'pointer'
                }}
              >
                Enter Terminal →
              </Badge>
            </Link>
          </Card>
        </Stack>
      </Container>
    </Layout>
  );
}