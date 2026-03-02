import Link from "next/link";

interface PageHeaderProps {
  ticker: string;
}

export default function PageHeader({ ticker }: PageHeaderProps) {
  console.log("PageHeader rendering, ticker:", ticker);
  const startYear = 2021;
  const endYear = 2025;

  return (
    <div className="w-full pb-6">
      <div className="flex items-start justify-between">
        <div>
          <Link
            href="/"
            className="mb-4 inline-block font-mono text-xs text-[#71717a] transition-colors hover:text-[#fafafa]"
          >
            ← Search
          </Link>
          <h1 style={{ fontSize: 32, fontWeight: 700, color: "#fafafa", margin: 0 }}>{ticker.toUpperCase()}</h1>
          <p style={{ marginTop: 8, fontFamily: "monospace", fontSize: 14, color: "#a1a1aa" }}>
            Annual Report Analysis · {startYear} – {endYear}
          </p>
        </div>
        <div className="rounded border border-[#27272a] bg-[#111113] px-2 py-1 font-mono text-xs text-[#71717a]">
          SEC 10-K
        </div>
      </div>
      <div className="mt-6 h-px w-full bg-[#27272a]" />
    </div>
  );
}
