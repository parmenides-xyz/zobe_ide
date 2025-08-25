'use client';

import { Container, Stack } from '@mantine/core';
import { Layout } from '@/components/Layout/Layout';
import ProposalList from '@/components/Proposals/ProposalList';

export default function HomePage() {
  return (
    <Layout>
      <Container p="md">
        <Stack gap="lg">
          <ProposalList />
        </Stack>
      </Container>
    </Layout>
  );
}
