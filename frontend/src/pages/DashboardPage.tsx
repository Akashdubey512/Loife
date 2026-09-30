import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Sidebar } from '../components/Sidebar';
import { ExecutiveDashboard } from '../dashboards/ExecutiveDashboard';
import { KitchenDashboard } from '../dashboards/KitchenDashboard';
import { QualityDashboard } from '../dashboards/QualityDashboard';
import { RedistributionDashboard } from '../dashboards/RedistributionDashboard';
import { LogisticsDashboard } from '../dashboards/LogisticsDashboard';
import { SustainabilityDashboard } from '../dashboards/SustainabilityDashboard';
import { DashboardTab } from '../types';
import { useAuth } from '../context/AuthContext';
import { getDefaultTab, canAccessTab } from '../utils/roleNav';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const defaultTab = user ? getDefaultTab(user.role) : 'executive';
  const [currentTab, setCurrentTab] = useState<DashboardTab>(defaultTab);

  // When the user role changes (e.g. persona switch), reset to the new default tab
  useEffect(() => {
    if (user) {
      const newDefault = getDefaultTab(user.role);
      setCurrentTab(newDefault);
    }
  }, [user?.role]);

  // Guard: if current tab is not allowed for this role, fall back to default
  const safeTab: DashboardTab =
    user && canAccessTab(user.role, currentTab) ? currentTab : defaultTab;

  const handleSelectTab = (tab: DashboardTab) => {
    if (user && canAccessTab(user.role, tab)) {
      setCurrentTab(tab);
    }
  };

  const renderActiveDashboard = () => {
    switch (safeTab) {
      case 'executive':       return <ExecutiveDashboard />;
      case 'kitchen':         return <KitchenDashboard />;
      case 'quality':         return <QualityDashboard />;
      case 'redistribution':  return <RedistributionDashboard />;
      case 'logistics':       return <LogisticsDashboard />;
      case 'sustainability':  return <SustainabilityDashboard />;
      default:                return <ExecutiveDashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-[#080b11] text-gray-100 flex flex-col font-sans selection:bg-[#F2C45A]/30 selection:text-[#FFF6E8]">
      {/* Top Header */}
      <Navbar
        activeTab={safeTab}
        onSelectPersonaTab={handleSelectTab}
      />

      {/* Main Layout Body */}
      <div className="flex-1 flex flex-row w-full overflow-hidden">
        {/* Left Navigation Sidebar */}
        <Sidebar currentTab={safeTab} onSelectTab={handleSelectTab} />

        {/* Dashboard Content Canvas */}
        <main className="flex-1 p-6 lg:p-8 overflow-y-auto max-h-[calc(100vh-61px)]">
          <div className="max-w-7xl mx-auto">
            {renderActiveDashboard()}
          </div>
        </main>
      </div>
    </div>
  );
};
