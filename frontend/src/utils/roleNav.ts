/**
 * Role-Based Navigation Utilities
 * Maps backend roles to dashboard tabs and authorised navigation items.
 * Derived from backend User model role constants.
 */
import { DashboardTab } from '../types';

export type UserRole =
  | 'SUPER_ADMIN'
  | 'ORG_ADMIN'
  | 'KITCHEN_MANAGER'
  | 'QUALITY_INSPECTOR'
  | 'LOGISTICS_COORDINATOR'
  | 'NGO_REP'
  | 'NGO_COORDINATOR'
  | 'LOGISTICS_DRIVER'
  | 'ESG_AUDITOR'
  | 'PUBLIC_USER'
  | string;

/**
 * Returns the dashboard tabs a given role is permitted to access.
 * SUPER_ADMIN and ORG_ADMIN see everything.
 */
export const getAllowedTabs = (role: UserRole): DashboardTab[] => {
  switch (role) {
    case 'SUPER_ADMIN':
    case 'ORG_ADMIN':
    case 'ESG_AUDITOR':
      return ['executive', 'kitchen', 'quality', 'redistribution', 'logistics', 'sustainability'];
    case 'KITCHEN_MANAGER':
      return ['kitchen', 'quality', 'sustainability'];
    case 'QUALITY_INSPECTOR':
      return ['quality', 'kitchen'];
    case 'LOGISTICS_COORDINATOR':
    case 'LOGISTICS_DRIVER':
      return ['logistics', 'redistribution'];
    case 'NGO_REP':
    case 'NGO_COORDINATOR':
      return ['redistribution'];
    default:
      // PUBLIC_USER or unknown — minimal access
      return ['executive'];
  }
};

/**
 * Returns the default landing tab for a given role.
 */
export const getDefaultTab = (role: UserRole): DashboardTab => {
  const allowed = getAllowedTabs(role);
  return allowed[0] ?? 'executive';
};

/**
 * Returns the frontend path for the role-specific dashboard.
 */
export const getRoleDashboardPath = (role: UserRole): string => {
  return '/dashboard';
};

/**
 * Returns true if the given role is allowed to access the given tab.
 */
export const canAccessTab = (role: UserRole, tab: DashboardTab): boolean => {
  return getAllowedTabs(role).includes(tab);
};
