import { NavLink, Stack, Text } from '@mantine/core';
import { IconChartLine, IconRobot, IconNetwork, IconBrain, IconTerminal2 } from '@tabler/icons-react';
import { useRouter, usePathname } from 'next/navigation';

export function NavigationLinks() {
  const router = useRouter();
  const pathname = usePathname();
  
  const navItems = [
    { 
      path: '/terminal', 
      label: 'Trading Terminal', 
      icon: IconTerminal2 
    }
  ];

  return (
    <Stack gap="xs">
      <Text 
        size="xs" 
        fw={600} 
        c="dimmed" 
        tt="uppercase" 
        style={{ 
          letterSpacing: '0.05em',
          marginBottom: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}
      >
        <IconBrain size={14} />
        Navigation
      </Text>
      
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = pathname === item.path;
        
        return (
          <NavLink
            key={item.path}
            href="#"
            onClick={() => router.push(item.path)}
            label={item.label}
            leftSection={<Icon size="1.1rem" stroke={1.5} />}
            active={isActive}
            style={{
              borderRadius: '12px',
              padding: '12px',
              background: isActive 
                ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.1))'
                : 'rgba(255, 255, 255, 0.03)',
              border: isActive 
                ? '1px solid rgba(102, 126, 234, 0.3)'
                : '1px solid rgba(255, 255, 255, 0.05)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              marginBottom: '4px'
            }}
            styles={{
              label: {
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#667eea' : undefined
              }
            }}
          />
        );
      })}
    </Stack>
  );
}
