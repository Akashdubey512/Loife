import React from 'react';

export interface LoifeLogoProps {
  variant?: 'horizontal' | 'icon' | 'stacked' | 'wordmark';
  theme?: 'dark' | 'light' | 'monochrome';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showTagline?: boolean;
  className?: string;
}

export const LoifeLogo: React.FC<LoifeLogoProps> = ({
  variant = 'horizontal',
  theme = 'dark',
  size = 'md',
  showTagline = false,
  className = '',
}) => {
  // Sizing configurations
  const sizeMap = {
    sm: { icon: 24, text: 'text-base', subtext: 'text-[9px]', gap: 'gap-2' },
    md: { icon: 36, text: 'text-xl', subtext: 'text-[10px]', gap: 'gap-2.5' },
    lg: { icon: 48, text: 'text-2xl', subtext: 'text-xs', gap: 'gap-3' },
    xl: { icon: 64, text: 'text-4xl', subtext: 'text-sm', gap: 'gap-3.5' },
  };

  const currentSize = sizeMap[size];

  // Theme palettes
  const isLight = theme === 'light';
  const isMono = theme === 'monochrome';

  // SVG Symbol: The Living Loaf
  // A rounded, golden loaf of bread with a gentle sprout emerging from its upper crest
  // and a subtle heart-shaped curve in the negative space.
  const LivingLoafIcon = (
    <svg
      width={currentSize.icon}
      height={currentSize.icon}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="shrink-0 transition-transform duration-300 hover:scale-105"
      aria-label="Loife Living Loaf Emblem"
    >
      <defs>
        {/* Loaf warm golden gradient */}
        <linearGradient id="loafGrad" x1="20" y1="35" x2="80" y2="85" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#F5D076" />
          <stop offset="50%" stopColor="#E2A645" />
          <stop offset="100%" stopColor="#C47832" />
        </linearGradient>

        {/* Sprout vitality green gradient */}
        <linearGradient id="sproutGrad" x1="50" y1="10" x2="75" y2="38" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#34D399" />
          <stop offset="100%" stopColor="#059669" />
        </linearGradient>

        {/* Soft shadow */}
        <filter id="loafGlow" x="0" y="0" width="100" height="100" filterUnits="userSpaceOnUse">
          <feDropShadow dx="0" dy="3" stdDeviation="3" floodColor="#E2A645" floodOpacity="0.25" />
        </filter>
      </defs>

      {/* Rounded Loaf Body with heart-contoured sharing base */}
      <path
        d="M24 64C18 64 14 59 14 51C14 38 29 32 50 32C71 32 86 38 86 51C86 59 82 64 76 64C71 64 67 61 63 58C59 55 54 53 50 53C46 53 41 55 37 58C33 61 29 64 24 64Z"
        fill={isMono ? 'currentColor' : 'url(#loafGrad)'}
        filter={isMono ? undefined : 'url(#loafGlow)'}
      />

      {/* Loaf scoring cuts — organic artisan bread marks */}
      <path
        d="M36 38C38 41 40 45 40 48"
        stroke={isLight ? '#8B6246' : '#FFF6E8'}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeOpacity="0.6"
      />
      <path
        d="M50 37C51 40 52 44 52 47"
        stroke={isLight ? '#8B6246' : '#FFF6E8'}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeOpacity="0.6"
      />
      <path
        d="M64 38C62 41 60 45 60 48"
        stroke={isLight ? '#8B6246' : '#FFF6E8'}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeOpacity="0.6"
      />

      {/* Sprout Stem rising from loaf crest */}
      <path
        d="M50 32C50 25 52 18 57 14"
        stroke={isMono ? 'currentColor' : 'url(#sproutGrad)'}
        strokeWidth="3.2"
        strokeLinecap="round"
      />

      {/* Primary Leaf (Right) */}
      <path
        d="M57 14C63 11 72 13 74 20C74 27 65 26 57 21"
        fill={isMono ? 'currentColor' : 'url(#sproutGrad)'}
      />

      {/* Secondary Leaf (Left / Heart accent) */}
      <path
        d="M52 23C46 20 40 22 41 27C42 32 49 30 52 26"
        fill={isMono ? 'currentColor' : 'url(#sproutGrad)'}
        fillOpacity="0.9"
      />

      {/* Subtle heart accent dot */}
      <circle cx="50" cy="68" r="2.5" fill={isMono ? 'currentColor' : '#F4A261'} fillOpacity="0.8" />
    </svg>
  );

  if (variant === 'icon') {
    return (
      <div className={`inline-flex items-center justify-center ${className}`}>
        {LivingLoafIcon}
      </div>
    );
  }

  // Wordmark typography
  const textColor = isMono
    ? 'text-current'
    : isLight
    ? 'text-[#174C3C]'
    : 'text-white';

  const sproutColor = isMono
    ? 'text-current'
    : isLight
    ? 'text-[#059669]'
    : 'text-emerald-400';

  const Wordmark = (
    <div className={`font-extrabold tracking-tight ${currentSize.text} ${textColor} select-none`}>
      <span>Lo</span>
      {/* The letter 'i' with a custom sprout leaf accent */}
      <span className="relative inline-block">
        <span className={sproutColor}>i</span>
        <svg
          className={`absolute -top-1.5 -right-0.5 pointer-events-none ${isMono ? 'text-current' : 'text-emerald-400'}`}
          width="8"
          height="8"
          viewBox="0 0 10 10"
          fill="currentColor"
        >
          <path d="M2 9C2 5 5 2 9 1C9 5 6 8 2 9Z" />
        </svg>
      </span>
      <span>fe</span>
    </div>
  );

  if (variant === 'wordmark') {
    return <div className={`inline-flex items-center ${className}`}>{Wordmark}</div>;
  }

  if (variant === 'stacked') {
    return (
      <div className={`inline-flex flex-col items-center text-center ${currentSize.gap} ${className}`}>
        {LivingLoafIcon}
        <div>
          {Wordmark}
          {showTagline && (
            <p className={`font-medium tracking-wide ${isLight ? 'text-[#8B6246]' : 'text-emerald-300/80'} ${currentSize.subtext} mt-0.5`}>
              Good Food. Shared Life.
            </p>
          )}
        </div>
      </div>
    );
  }

  // Horizontal variant (default)
  return (
    <div className={`inline-flex items-center ${currentSize.gap} ${className}`}>
      {LivingLoafIcon}
      <div className="flex flex-col">
        <div className="flex items-center gap-2">
          {Wordmark}
        </div>
        {showTagline && (
          <p className={`font-medium tracking-wide ${isLight ? 'text-[#8B6246]' : 'text-gray-400'} ${currentSize.subtext} leading-none mt-0.5`}>
            Good Food. Shared Life.
          </p>
        )}
      </div>
    </div>
  );
};

export default LoifeLogo;
