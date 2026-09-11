export type Player = {
  player_id: string;
  name: string;
  stack: number;
  cards: string[];
  bet: number;
  folded: boolean;
  connected: boolean;
};

export type TableState = {
  table_id: string;
  street: string;
  community: string[];
  pot: number;
  current_bet: number;
  turn_player_id: string | null;
  players: Player[];
  hand_id: string | null;
  commitment: string | null;
  audit: Record<string, unknown> | null;
};

