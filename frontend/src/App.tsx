import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { ExecutiveDashboard } from './dashboards/ExecutiveDashboard';
import { KitchenDashboard } from './dashboards/KitchenDashboard';
import { QualityDashboard } from './dashboards/QualityDashboard';
import { RedistributionDashboard } from './dashboards/RedistributionDashboard';
import { LogisticsDashboard } from './dashboards/LogisticsDashboard';
import { SustainabilityDashboard } from './dashboards/SustainabilityDashboard';
import { DashboardTab } from './types';
import './App.css';

export function App() {
  const [currentTab, setCurrentTab] = useState<DashboardTab>('executive');

  const renderActiveDashboard = () => {
    switch (currentTab) {
      case 'executive':
        return <ExecutiveDashboard />;
      case 'kitchen':
        return <KitchenDashboard />;
      case 'quality':
        return <QualityDashboard />;
      case 'redistribution':
        return <RedistributionDashboard />;
      case 'logistics':
        return <LogisticsDashboard />;
      case 'sustainability':
        return <SustainabilityDashboard />;
      default:
        return <ExecutiveDashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-[#080b11] text-gray-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-gray-950">
      {/* Top Header */}
      <Navbar activeTab={currentTab} />

      {/* Main Layout Body */}
      <div className="flex-1 flex flex-row w-full overflow-hidden">
        {/* Left Navigation Sidebar */}
        <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />

        {/* Dashboard Content Canvas */}
        <main className="flex-1 p-6 lg:p-8 overflow-y-auto max-h-[calc(100vh-61px)]">
          <div className="max-w-7xl mx-auto">
            {renderActiveDashboard()}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
