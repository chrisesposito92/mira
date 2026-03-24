// Canvas dimensions
export const CANVAS_WIDTH = 1200;
export const CANVAS_HEIGHT = 800;
export const CANVAS_PADDING = 40;

// Hub node
export const HUB_RADIUS = 80;
export const HUB_CENTER_X = 600;
export const HUB_CENTER_Y = 400;

// Prospect node
export const PROSPECT_Y = 60;

// System cards
export const SYSTEM_CARD_WIDTH = 120;
export const SYSTEM_CARD_HEIGHT = 100;

// Group cards
export const GROUP_CARD_PADDING = 16;
export const GROUP_CARD_GAP = 12;
export const LOGO_SIZE = 36;
export const LOGO_GRID_COLS = 2;

// Card styling
export const CARD_BORDER_RADIUS = 12;
export const CARD_SHADOW_OFFSET = 2;
export const CARD_SHADOW_BLUR = 8;

// Connection pills
export const PILL_PADDING_X = 10;
export const PILL_PADDING_Y = 4;
export const PILL_BORDER_RADIUS = 10;

// Connection lines
export const CONNECTION_DOT_RADIUS = 4;
export const ARROWHEAD_SIZE = 8;
export const CONNECTION_STROKE_WIDTH = 2;
export const CONNECTION_DASH = '6,4';

// SVG Colors (inline hex -- never Tailwind)
export const CANVAS_BG = '#1a1f36';
export const CARD_BG = '#FFFFFF';
export const CARD_SHADOW = 'rgba(0,0,0,0.15)';
export const CARD_BORDER = '#E2E8F0';
export const HUB_BG = '#FFFFFF';
export const HUB_ACCENT_BORDER = '#00C853';
export const HUB_ACCENT_BORDER_WIDTH = 3;
export const PROSPECT_BG = '#FFFFFF';
export const PROSPECT_BORDER = '#94A3B8';
export const TEXT_PRIMARY = '#1E293B';
export const TEXT_SECONDARY = '#64748B';
export const TEXT_ON_DARK = '#FFFFFF';
export const PILL_TEXT = '#FFFFFF';
export const MONOGRAM_TEXT = '#FFFFFF';

// Connection type color map (CONN-04)
export const CONNECTION_COLORS: Record<string, string> = {
	native_connector: '#00C853',
	webhook_api: '#2196F3',
	custom_build: '#FF9800',
	api: '#90A4AE',
};

// SVG font family
export const SVG_FONT_FAMILY = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";

// m3ter hub capabilities
export const HUB_CAPABILITIES = [
	'Usage',
	'Pricing',
	'Rating',
	'Credits',
	'Alerts',
	'Limits',
] as const;

// Text truncation defaults
export const MAX_SYSTEM_NAME_CHARS = 16;
export const MAX_PILL_LABEL_CHARS = 24;
export const MAX_CATEGORY_NAME_CHARS = 20;
