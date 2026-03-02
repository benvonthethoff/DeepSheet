const GREEN = "#4ade80";
const RED = "#fb7185";
const DIM = "#e4e4e7";

interface DerivedEntry {
  year: number;
  fcf: number | null;
  grossMarginPct: number | null;
  revenueGrowthPct: number | null;
}

interface Signal {
  year: number;
  flags: string[];
}

interface DataEntry {
  year: number;
  val: number | null;
}

interface FinancialsData {
  derived: DerivedEntry[];
  signals: {
    revenueSignals: Signal[];
    marginSignals: Signal[];
    fcfSignals: Signal[];
  };
  NetIncomeLoss: DataEntry[];
  PaymentsToAcquirePropertyPlantAndEquipment: DataEntry[];
}

interface FinancialTableProps {
  data: FinancialsData;
}

function fmtPct(val: number | null): string {
  if (val == null) return "—";
  return `${val > 0 ? "+" : ""}${val.toFixed(1)}%`;
}

function fmtB(val: number | null): string {
  if (val == null) return "—";
  return `$${(val / 1e9).toFixed(1)}B`;
}

function revenueColor(flags: string[]): string {
  if (flags.includes("declining")) return RED;
  if (flags.includes("accelerating")) return GREEN;
  if (flags.includes("stable")) return DIM;
  return DIM;
}

function marginColor(flags: string[]): string {
  if (flags.includes("expanding")) return GREEN;
  if (flags.includes("compressing")) return RED;
  return DIM;
}

function fcfColor(flags: string[]): string {
  if (flags.includes("fcf_exceeds_net_income")) return GREEN;
  if (flags.includes("fcf_below_net_income")) return RED;
  return DIM;
}

function yoyColor(curr: number | null, prev: number | null): string {
  if (curr == null || prev == null) return DIM;
  return curr > prev ? GREEN : curr < prev ? RED : DIM;
}

export default function FinancialTable({ data }: FinancialTableProps) {
  const { derived, signals } = data;

  const revMap = Object.fromEntries(signals.revenueSignals.map(s => [s.year, s]));
  const margMap = Object.fromEntries(signals.marginSignals.map(s => [s.year, s]));
  const fcfMap = Object.fromEntries(signals.fcfSignals.map(s => [s.year, s]));
  const niMap = Object.fromEntries(data.NetIncomeLoss.map(e => [e.year, e.val]));
  const capexMap = Object.fromEntries(data.PaymentsToAcquirePropertyPlantAndEquipment.map(e => [e.year, e.val]));

  const years = derived.map(d => d.year);

  const rows = [
    {
      label: "Revenue Growth",
      values: derived.map(d => fmtPct(d.revenueGrowthPct)),
      colors: derived.map(d => revenueColor((revMap[d.year] as Signal)?.flags ?? [])),
    },
    {
      label: "Gross Margin",
      values: derived.map(d => fmtPct(d.grossMarginPct)),
      colors: derived.map(d => marginColor((margMap[d.year] as Signal)?.flags ?? [])),
    },
    {
      label: "Free Cash Flow",
      values: derived.map(d => fmtB(d.fcf)),
      colors: derived.map(d => fcfColor((fcfMap[d.year] as Signal)?.flags ?? [])),
    },
    {
      label: "Net Income",
      values: derived.map(d => fmtB(niMap[d.year] as number | null)),
      colors: derived.map((d, i) => {
        const curr = (niMap[d.year] as number | null) ?? null;
        const prev = i > 0 ? ((niMap[derived[i - 1].year] as number | null) ?? null) : null;
        return yoyColor(curr, prev);
      }),
    },
    {
      label: "Capex",
      values: derived.map(d => fmtB(capexMap[d.year] as number | null)),
      colors: derived.map((d, i) => {
        const curr = (capexMap[d.year] as number | null) ?? null;
        const prev = i > 0 ? ((capexMap[derived[i - 1].year] as number | null) ?? null) : null;
        return yoyColor(prev, curr);
      }),
    },
  ];

  return (
    <div>
      <h2 style={{ fontSize: 18, fontWeight: 600, color: "#fafafa", marginBottom: 16 }}>Key Metrics</h2>
      <div style={{ border: "1px solid #27272a", borderRadius: 8, overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: "160px repeat(5, 1fr)", background: "#111113", borderBottom: "1px solid #27272a" }}>
          <div style={{ padding: "12px 16px" }} />
          {years.map(y => (
            <div key={y} style={{ padding: "12px 8px", textAlign: "right", fontSize: 12, color: "#d4d4d8", fontFamily: "'IBM Plex Mono', monospace", letterSpacing: "0.05em", fontWeight: 500 }}>
              {y}
            </div>
          ))}
        </div>
        {rows.map((row, ri) => (
          <div key={row.label} style={{ display: "grid", gridTemplateColumns: "160px repeat(5, 1fr)", borderBottom: ri < rows.length - 1 ? "1px solid #27272a" : "none", background: ri % 2 === 0 ? "transparent" : "#0d0d0f" }}>
            <div style={{ padding: "16px 16px", display: "flex", alignItems: "center" }}>
              <span style={{ fontSize: 12, color: "#e4e4e7", fontFamily: "'IBM Plex Sans', sans-serif", fontWeight: 500 }}>{row.label}</span>
            </div>
            {row.values.map((val, ci) => {
              const dotColor = row.colors[ci];
              const showDot = ci > 0 && dotColor !== "#e4e4e7";
              return (
                <div key={ci} style={{ padding: "14px 8px 12px", textAlign: "right" }}>
                  <span style={{ fontSize: 13, color: "#e4e4e7", fontFamily: "'IBM Plex Mono', monospace", fontWeight: 500 }}>{val}</span>
                  <div style={{ height: 6, display: "flex", justifyContent: "flex-end", marginTop: 4 }}>
                    {showDot && <div style={{ width: 5, height: 5, borderRadius: "50%", background: dotColor }} />}
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <div style={{ marginTop: 16, display: "flex", gap: 20, justifyContent: "flex-end" }}>
        {[["#4ade80", "↑ YoY increase"], ["#fb7185", "↓ YoY decrease"]].map(([color, label]) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: color }} />
            <span style={{ fontSize: 10, color: "#71717a", fontFamily: "'IBM Plex Mono', monospace" }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
