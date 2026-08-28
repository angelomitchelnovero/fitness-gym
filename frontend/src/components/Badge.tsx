import type { ReactNode } from 'react';

import { cn } from '@/lib/utils';

type Variant = 'default' | 'secondary' | 'destructive' | 'success' | 'warning';

interface Props {
  variant?: Variant;
  children: ReactNode;
  className?: string;
}

const variants: Record<Variant, string> = {
  default: 'bg-primary/15 text-primary',
  secondary: 'bg-secondary text-secondary-foreground',
  destructive: 'bg-destructive/15 text-destructive',
  success: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
  warning: 'bg-amber-500/15 text-amber-700 dark:text-amber-300',
};

export function Badge({ variant = 'default', children, className }: Props) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
