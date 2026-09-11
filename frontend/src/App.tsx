import { FormEvent, useMemo, useState } from "react";
import { useTable } from "./useTable";
import "./styles.css";

function Card({ value }: { value: string }) {
  return <span className={value.endsWith("h") || value.endsWith("d") ? "card red" : "card"}>{value}</span>;
}

export default function App() {
  const [identity, setIdentity] = useState({ table: "demo", player: crypto.randomUUID().slice(0, 8), name: "Player" });
  const [joined, setJoined] = useState(false);
  const [raise, setRaise] = useState(20);
  const { table, error, send } = useTable(joined ? identity.table : "", identity.player);
  const me = useMemo(() => table?.players.find((player) => player.player_id === identity.player), [table, identity.player]);

  async function join(event: FormEvent) {
    event.preventDefault();
    const base = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
    await fetch(`${base}/tables/${identity.table}/players`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ player_id: identity.player, display_name: identity.name, stack: 1000 }),
    });
    setJoined(true);
  }

  if (!joined) {
    return <main className="shell"><form className="panel join" onSubmit={join}><p className="eyebrow">RIVER ROOM</p><h1>Take a seat.</h1><label>Table<input value={identity.table} onChange={(e) => setIdentity({ ...identity, table: e.target.value })} /></label><label>Name<input value={identity.name} onChange={(e) => setIdentity({ ...identity, name: e.target.value })} /></label><button>Join table</button></form></main>;
  }

  return <main className="shell"><header><div><p className="eyebrow">TABLE {identity.table}</p><h1>{table?.street ?? "Connecting"}</h1></div><strong>{me?.stack ?? 0} chips</strong></header>{error && <p className="error">{error}</p>}<section className="felt"><div className="community">{table?.community.map((card) => <Card key={card} value={card} />)}</div><div className="pot">Pot · {table?.pot ?? 0}</div><div className="seats">{table?.players.map((player) => <article className={player.player_id === table.turn_player_id ? "seat active" : "seat"} key={player.player_id}><span>{player.name}</span><small>{player.stack} · bet {player.bet}{player.folded ? " · folded" : ""}</small></article>)}</div></section><section className="hand"><div>{me?.cards.map((card) => <Card key={card} value={card} />)}</div><div className="actions"><button onClick={() => send({ type: "action", action: "fold" })}>Fold</button><button onClick={() => send({ type: "action", action: "check" })}>Check</button><button onClick={() => send({ type: "action", action: "call" })}>Call</button><input type="number" value={raise} onChange={(e) => setRaise(Number(e.target.value))} /><button onClick={() => send({ type: "action", action: "raise", amount: raise })}>Raise</button></div></section><footer><code>{table?.commitment?.slice(0, 20)}…</code><button className="quiet" onClick={() => send({ type: "start", entropy: { [identity.player]: crypto.randomUUID() } })}>Start hand</button></footer></main>;
}

