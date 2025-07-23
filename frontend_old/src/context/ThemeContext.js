import React, { createContext, useContext, useState, useEffect } from 'react';
import { ConfigProvider, theme } from 'antd';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

// SCARLET Protocol inspired theme
const scarletTheme = {
  // Primary colors
  colorPrimary: '#ff0040',
  colorPrimaryBg: '#1a0000',
  colorPrimaryBgHover: '#330000',
  colorPrimaryBorder: '#660000',
  colorPrimaryBorderHover: '#990000',
  colorPrimaryHover: '#ff3366',
  colorPrimaryActive: '#cc0033',
  
  // Base colors
  colorBgBase: '#000000',
  colorBgContainer: '#0a0000',
  colorBgElevated: '#1a0000',
  colorBgLayout: '#000000',
  colorBgSpotlight: '#330000',
  colorBgMask: 'rgba(0, 0, 0, 0.85)',
  
  // Text colors
  colorText: '#ff6666',
  colorTextBase: '#ff6666',
  colorTextSecondary: '#cc4444',
  colorTextTertiary: '#993333',
  colorTextQuaternary: '#662222',
  colorTextPlaceholder: '#661111',
  colorTextDisabled: '#440000',
  colorTextHeading: '#ff0040',
  colorTextLabel: '#ff4466',
  colorTextDescription: '#cc4444',
  colorTextLightSolid: '#000000',
  
  // Border colors
  colorBorder: '#330000',
  colorBorderSecondary: '#220000',
  colorSplit: '#1a0000',
  
  // State colors
  colorSuccess: '#00ff00',
  colorSuccessBg: '#001a00',
  colorSuccessBgHover: '#003300',
  colorSuccessBorder: '#006600',
  colorSuccessBorderHover: '#009900',
  colorSuccessHover: '#33ff33',
  colorSuccessActive: '#00cc00',
  
  colorWarning: '#ffaa00',
  colorWarningBg: '#1a0d00',
  colorWarningBgHover: '#331a00',
  colorWarningBorder: '#663300',
  colorWarningBorderHover: '#994d00',
  colorWarningHover: '#ffbb33',
  colorWarningActive: '#cc8800',
  
  colorError: '#ff0040',
  colorErrorBg: '#1a0000',
  colorErrorBgHover: '#330000',
  colorErrorBorder: '#660000',
  colorErrorBorderHover: '#990000',
  colorErrorHover: '#ff3366',
  colorErrorActive: '#cc0033',
  
  colorInfo: '#ff0040',
  colorInfoBg: '#1a0000',
  colorInfoBgHover: '#330000',
  colorInfoBorder: '#660000',
  colorInfoBorderHover: '#990000',
  colorInfoHover: '#ff3366',
  colorInfoActive: '#cc0033',
  
  // Other colors
  colorLink: '#ff0040',
  colorLinkHover: '#ff3366',
  colorLinkActive: '#cc0033',
  
  colorFill: '#1a0000',
  colorFillSecondary: '#0d0000',
  colorFillTertiary: '#080000',
  colorFillQuaternary: '#040000',
  
  colorBgTextHover: '#1a0000',
  colorBgTextActive: '#330000',
  
  // Component specific
  controlOutline: 'rgba(255, 0, 64, 0.2)',
  controlItemBgActive: '#330000',
  controlItemBgActiveHover: '#4d0000',
  controlItemBgHover: '#1a0000',
  
  // Sizes
  borderRadius: 2,
  borderRadiusLG: 4,
  borderRadiusSM: 2,
  
  // Font
  fontFamily: '"Fira Code", "Monaco", "Menlo", "Consolas", monospace',
  fontSize: 16,
  fontSizeLG: 18,
  fontSizeSM: 14,
  
  // Motion
  motionDurationFast: '0.1s',
  motionDurationMid: '0.2s',
  motionDurationSlow: '0.3s',
};

export const ThemeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('scarletDarkMode');
    return saved === 'true';
  });

  useEffect(() => {
    localStorage.setItem('scarletDarkMode', isDarkMode);
    
    // Add or remove dark mode class on body
    if (isDarkMode) {
      document.body.classList.add('scarlet-dark-mode');
    } else {
      document.body.classList.remove('scarlet-dark-mode');
    }
  }, [isDarkMode]);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  const themeConfig = isDarkMode ? {
    algorithm: theme.darkAlgorithm,
    token: scarletTheme,
    components: {
      Layout: {
        headerBg: '#000000',
        bodyBg: '#000000',
        triggerBg: '#1a0000',
      },
      Menu: {
        colorBgContainer: '#0a0000',
        itemBg: '#0a0000',
        itemHoverBg: '#1a0000',
        itemActiveBg: '#330000',
        itemSelectedBg: '#330000',
        itemColor: '#ff6666',
        itemHoverColor: '#ff0040',
        itemActiveColor: '#ff0040',
        itemSelectedColor: '#ff0040',
        subMenuItemBg: '#000000',
      },
      Card: {
        colorBgContainer: '#0a0000',
        colorBorderSecondary: '#330000',
      },
      Button: {
        colorPrimary: '#ff0040',
        colorPrimaryHover: '#ff3366',
        colorPrimaryActive: '#cc0033',
        colorBgContainer: '#1a0000',
        colorBorder: '#660000',
        defaultBorderColor: '#330000',
        defaultColor: '#ff6666',
        defaultBg: '#0a0000',
      },
      Input: {
        colorBgContainer: '#0a0000',
        colorBorder: '#330000',
        colorText: '#ff6666',
        colorTextPlaceholder: '#661111',
        activeBorderColor: '#ff0040',
        hoverBorderColor: '#660000',
      },
      Table: {
        colorBgContainer: '#0a0000',
        colorBorderSecondary: '#330000',
        headerBg: '#1a0000',
        rowHoverBg: '#1a0000',
        colorText: '#ff6666',
      },
      Progress: {
        defaultColor: '#ff0040',
        remainingColor: '#1a0000',
      },
      Tag: {
        defaultBg: '#1a0000',
        defaultColor: '#ff6666',
      },
      Alert: {
        colorErrorBg: '#1a0000',
        colorErrorBorder: '#660000',
        colorInfoBg: '#1a0000',
        colorInfoBorder: '#660000',
        colorSuccessBg: '#001a00',
        colorSuccessBorder: '#006600',
        colorWarningBg: '#1a0d00',
        colorWarningBorder: '#663300',
      },
      Timeline: {
        colorText: '#ff6666',
        colorBgContainer: 'transparent',
        colorSplit: '#330000',
      },
      Tree: {
        colorBgContainer: 'transparent',
        nodeHoverBg: '#1a0000',
        nodeSelectedBg: '#330000',
      },
      Breadcrumb: {
        colorText: '#cc4444',
        colorTextDescription: '#993333',
        colorBgTextHover: '#1a0000',
        linkColor: '#ff0040',
        linkHoverColor: '#ff3366',
      },
      Spin: {
        colorPrimary: '#ff0040',
      },
      Divider: {
        colorSplit: '#330000',
      },
      Typography: {
        colorText: '#ff6666',
        colorTextHeading: '#ff0040',
        colorTextSecondary: '#cc4444',
        colorTextDisabled: '#440000',
        colorLink: '#ff0040',
        colorLinkHover: '#ff3366',
        colorLinkActive: '#cc0033',
      },
      Statistic: {
        colorText: '#ff6666',
        contentFontSize: 20,
      },
      Select: {
        colorBgContainer: '#0a0000',
        colorBorder: '#330000',
        colorText: '#ff6666',
        colorTextPlaceholder: '#661111',
        optionSelectedBg: '#330000',
        optionActiveBg: '#1a0000',
      },
      Checkbox: {
        colorPrimary: '#ff0040',
        colorBgContainer: '#0a0000',
        colorBorder: '#330000',
        colorWhite: '#000000',
      },
      Tooltip: {
        colorBgSpotlight: '#1a0000',
        colorTextLightSolid: '#ff6666',
      },
      Modal: {
        colorBgElevated: '#0a0000',
        headerBg: '#1a0000',
        contentBg: '#0a0000',
        footerBg: '#0a0000',
      },
      Notification: {
        colorBgElevated: '#1a0000',
        colorText: '#ff6666',
        colorTextHeading: '#ff0040',
        colorIcon: '#ff0040',
        colorIconHover: '#ff3366',
      },
    }
  } : {
    token: {
      colorPrimary: '#1890ff',
      borderRadius: 6,
    },
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme }}>
      <ConfigProvider theme={themeConfig}>
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
};