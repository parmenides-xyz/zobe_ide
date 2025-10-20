'use client';

import {
  AppShell,
  Burger,
  Flex,
  Group,
  Title,
  Badge,
  useMantineTheme,
} from '@mantine/core';
import { useDisclosure, useMediaQuery } from '@mantine/hooks';
import '@mantine/notifications/styles.css';
import Image from 'next/image';
import Link from 'next/link';
import React from 'react';
import icon from '@/public/bg-fire.png';
import { NavigationLinks } from './NavigationLinks';

export type LayoutProps = {
  children: React.ReactNode;
};

export function Layout(props: LayoutProps) {
  const { children } = props;
  const theme = useMantineTheme();
  const isTiny = useMediaQuery(`(max-width: ${theme.breakpoints.xs})`);
  const [mobileOpened, { toggle: toggleMobile }] = useDisclosure();
  const [desktopOpened, { toggle: toggleDesktop }] = useDisclosure(false);

  return (
    <div>
      <AppShell
        header={{ height: 70 }}
        navbar={{ breakpoint: 'md', width: 220, collapsed: { mobile: !mobileOpened, desktop: !desktopOpened } }}
        padding="md"
        styles={{
          header: {
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.1))',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderTop: 'none',
            borderLeft: 'none',
            borderRight: 'none'
          },
          navbar: {
            background: 'linear-gradient(180deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.05))',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderTop: 'none',
            borderBottom: 'none',
            borderLeft: 'none'
          }
        }}
      >
        <AppShell.Header>
          <Flex justify="space-between" align="center" p="lg" w="100%" h="100%">
            <Group p={0} m={0}>
              <Burger 
                opened={mobileOpened} 
                onClick={toggleMobile} 
                hiddenFrom="sm" 
                size="sm"
                style={{ 
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px'
                }}
              />
              <Burger 
                opened={desktopOpened} 
                onClick={toggleDesktop} 
                visibleFrom="sm" 
                size="sm"
                style={{ 
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px'
                }}
              />
              <Link href="/" style={{ textDecoration: 'none', color: 'inherit' }}>
                <Flex justify="flex-start" align="center" gap="xs">
                  <div style={{
                    padding: '8px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderRadius: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Image src={icon} alt="Zobeide logo" width={28} height={28} style={{ filter: 'brightness(0) invert(1)' }} />
                  </div>
                  <Title
                    order={!isTiny ? 3 : 4}
                    style={{
                      color: 'white',
                      fontWeight: 700
                    }}
                  >
                    Zobeide
                  </Title>
                </Flex>
              </Link>
            </Group>


            <div />
          </Flex>
        </AppShell.Header>
        
        <AppShell.Navbar p="lg">
          <div style={{
            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02))',
            borderRadius: '16px',
            padding: '16px',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            height: '100%'
          }}>
            <NavigationLinks />
          </div>
        </AppShell.Navbar>
        
        <AppShell.Main>{children}</AppShell.Main>
      </AppShell>
    </div>
  );
}