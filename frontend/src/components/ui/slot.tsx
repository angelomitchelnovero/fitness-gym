import * as React from 'react';

/**
 * Minimal Slot implementation that merges props onto its single child.
 * Replaces `@radix-ui/react-slot` until we add Radix primitives later.
 */
export type SlotProps = React.HTMLAttributes<HTMLElement> & {
  children?: React.ReactNode;
};

function mergeProps(
  childProps: Record<string, unknown>,
  slotProps: Record<string, unknown>,
): Record<string, unknown> {
  const merged: Record<string, unknown> = { ...childProps, ...slotProps };
  for (const key of Object.keys(slotProps)) {
    const a = childProps[key];
    const b = slotProps[key];
    if (typeof a === 'function' && typeof b === 'function') {
      merged[key] = (...args: unknown[]) => {
        const resultA = (a as (...args: unknown[]) => unknown)(...args);
        const resultB = (b as (...args: unknown[]) => unknown)(...args);
        return typeof resultB === 'function' ? resultB : resultA;
      };
    }
  }
  return merged;
}

export const Slot = React.forwardRef<HTMLElement, SlotProps>(
  ({ children, ...slotProps }, ref) => {
    if (!React.isValidElement(children)) {
      return null;
    }
    const child = children as React.ReactElement<Record<string, unknown>>;
    const childProps = child.props ?? {};
    return React.cloneElement(child, {
      ...mergeProps(childProps, slotProps as Record<string, unknown>),
      ref,
    } as Record<string, unknown>);
  },
);
Slot.displayName = 'Slot';
