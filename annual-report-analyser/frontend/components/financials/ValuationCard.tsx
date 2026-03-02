import { FinancialsData } from "@/types/financials";

interface ValuationCardProps {
  data: FinancialsData;
}

function fmtPrice(val: number | null, currency: string | null) {
  if (val == null) return "—";
  const symbol = currency === "USD" ? "$" : currency ?? "$";
  return `${symbol}${val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtMarketCap(val: number | null) {
  if (val == null) return "—";
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
  return `$${(val / 1e6).toFixed(0)}M`;
}

function fmtMultiple(val: number | null) {
  if (val == null) return "—";
  return `${val.toFixed(1)}×`;
}

export default function ValuationCard({ data }: ValuationCardProps) {
  const metrics = [
    { label: "PRICE", value: fmtPrice(data.stockData?.price, data.stockData?.currency), isNull: data.stockData?.price == null },
    { label: "MARKET CAP", value: fmtMarketCap(data.stockData?.marketCap), isNull: data.stockData?.marketCap == null },
    { label: "P/E", value: fmtMultiple(data.valuationRatios?.peRatio), isNull: data.valuationRatios?.peRatio == null },
    { label: "PRICE / FCF", value: fmtMultiple(data.valuationRatios?.priceFCF), isNull: data.valuationRatios?.priceFCF == null },
  ];

  return (
    <div style={{ display: "flex", border: "1px solid #27272a", borderRadius: 8, background: "#111113", overflow: "hidden", marginBottom: 24 }}>
      {metrics.map((metric, i) => (
        <div
          key={metric.label}
          style={{
            flex: 1,
            padding: "16px 20px",
            borderRight: i < metrics.length - 1 ? "1px solid #27272a" : "none",
          }}
        >
          <div style={{ fontSize: 10, fontFamily: "'IBM Plex Mono', monospace", color: "#52525b", letterSpacing: "0.05em", marginBottom: 6 }}>
            {metric.label}
          </div>
          <div style={{ fontSize: 18, fontFamily: "'IBM Plex Mono', monospace", fontWeight: 500, color: metric.isNull ? "#3f3f46" : "#e4e4e7" }}>
            {metric.value}
          </div>
        </div>
      ))}
    </div>
  );
}
