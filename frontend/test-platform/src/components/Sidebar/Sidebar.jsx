import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Play, History, ChevronLeft, ChevronRight, LayoutDashboard, FileJson, FilePlus2, AppWindow, ListChecks, Sun, Moon } from 'lucide-react';

const NAV_ITEMS = [
    { label: 'Run Tests',       to: '/',                icon: <Play size={18} /> },
    { label: 'Add Test Case',   to: '/add-test-case',    icon: <FilePlus2 size={18} /> },
    { label: 'Test Cases',      to: '/test-cases',       icon: <ListChecks size={18} /> },
    { label: 'Apps & Modules',  to: '/add-app-module',   icon: <AppWindow size={18} /> },
    // { label: 'API Matrix',   to: '/api-matrix',  icon: <Zap size={18} /> },
    { label: 'API Batch',       to: '/api-batch',        icon: <FileJson size={18} /> },
    { label: 'Jira History',    to: '/jira-history',     icon: <History size={18} /> },
];

// Apply the persisted theme as early as possible (module load) to avoid a flash.
const getInitialTheme = () => {
    try {
        const saved = localStorage.getItem('theme');
        if (saved === 'dark' || saved === 'light') return saved;
        return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    } catch {
        return 'light';
    }
};

export default function Sidebar() {
    const [collapsed, setCollapsed] = useState(false);
    const [theme, setTheme] = useState(getInitialTheme);

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        try { localStorage.setItem('theme', theme); } catch { /* ignore */ }
    }, [theme]);

    const isDark = theme === 'dark';

    return (
        <aside style={{
            width: collapsed ? '60px' : '210px',
            height: '100vh',
            background: 'var(--bg-sidebar)',
            borderRight: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            transition: 'width 0.22s ease',
            overflow: 'hidden',
            flexShrink: 0,
            boxShadow: 'var(--shadow-xs)',
        }}>

            {/* ── Brand + theme toggle ── */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: collapsed ? '18px 0' : '18px 12px 16px 16px',
                borderBottom: '1px solid var(--border-color)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                justifyContent: collapsed ? 'center' : 'flex-start',
            }}>
                <div style={{
                    width: '32px', height: '32px',
                    background: 'linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)',
                    borderRadius: '8px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0,
                    boxShadow: '0 2px 6px rgba(37,99,235,0.3)',
                }}>
                    <LayoutDashboard size={17} color="#fff" />
                </div>
                {!collapsed && (
                    <div style={{ minWidth: 0, flex: 1 }}>
                        <div style={{
                            color: 'var(--text-primary)',
                            fontWeight: 800,
                            fontSize: '13.5px',
                            letterSpacing: '-0.01em',
                            lineHeight: '1.2',
                        }}>
                            TAP / Android
                        </div>
                        <div style={{
                            color: 'var(--text-muted)',
                            fontSize: '10px',
                            marginTop: '2px',
                            lineHeight: '1.35',
                        }}>
                            Test Automation Platform
                        </div>
                    </div>
                )}
                {!collapsed && (
                    <button
                        onClick={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))}
                        title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
                        aria-label="Toggle color theme"
                        style={{
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            width: '30px', height: '30px', flexShrink: 0,
                            background: 'var(--bg-input)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '8px',
                            color: 'var(--text-secondary)',
                            cursor: 'pointer',
                            transition: 'color 0.15s, background 0.15s',
                        }}
                        onMouseEnter={e => { e.currentTarget.style.color = 'var(--accent-blue)'; }}
                        onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-secondary)'; }}
                    >
                        {isDark ? <Sun size={16} /> : <Moon size={16} />}
                    </button>
                )}
            </div>

            {/* ── Nav Items ── */}
            <nav style={{ flex: 1, padding: '10px 8px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                {NAV_ITEMS.map(({ label, to, icon }) => (
                    <NavLink
                        key={to}
                        to={to}
                        title={collapsed ? label : undefined}
                        style={({ isActive }) => ({
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                            padding: collapsed ? '10px 0' : '9px 12px',
                            justifyContent: collapsed ? 'center' : 'flex-start',
                            borderRadius: '8px',
                            textDecoration: 'none',
                            color: isActive ? 'var(--accent-blue)' : 'var(--text-secondary)',
                            background: isActive ? 'var(--accent-blue-light)' : 'transparent',
                            fontWeight: isActive ? 700 : 500,
                            fontSize: '13px',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            transition: 'background 0.15s, color 0.15s',
                            borderLeft: isActive ? '3px solid var(--accent-blue)' : '3px solid transparent',
                        })}
                        onMouseEnter={e => {
                            // Leave the active item styled; only hover the inactive ones.
                            if (e.currentTarget.getAttribute('aria-current') !== 'page') {
                                e.currentTarget.style.background = 'var(--bg-input)';
                                e.currentTarget.style.color = 'var(--text-primary)';
                            }
                        }}
                        onMouseLeave={e => {
                            if (e.currentTarget.getAttribute('aria-current') !== 'page') {
                                e.currentTarget.style.background = 'transparent';
                                e.currentTarget.style.color = 'var(--text-secondary)';
                            }
                        }}
                    >
                        <span style={{ flexShrink: 0 }}>{icon}</span>
                        {!collapsed && <span>{label}</span>}
                    </NavLink>
                ))}
            </nav>

            {/* ── Footer: theme (when collapsed) + collapse toggle ── */}
            {collapsed && (
                <button
                    onClick={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))}
                    title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
                    aria-label="Toggle color theme"
                    style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        padding: '10px 0', background: 'none', border: 'none',
                        borderTop: '1px solid var(--border-color)',
                        color: 'var(--text-muted)', cursor: 'pointer',
                    }}
                >
                    {isDark ? <Sun size={16} /> : <Moon size={16} />}
                </button>
            )}
            <button
                onClick={() => setCollapsed(c => !c)}
                title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: collapsed ? 'center' : 'flex-end',
                    gap: '6px',
                    padding: '12px 16px',
                    background: 'none',
                    border: 'none',
                    borderTop: '1px solid var(--border-color)',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontFamily: 'inherit',
                    whiteSpace: 'nowrap',
                    transition: 'color 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-secondary)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; }}
            >
                {collapsed ? <ChevronRight size={16} /> : (
                    <>
                        <span style={{ fontSize: '12px', fontWeight: 500 }}>Collapse</span>
                        <ChevronLeft size={16} />
                    </>
                )}
            </button>
        </aside>
    );
}
