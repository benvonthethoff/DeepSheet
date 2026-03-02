"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import PageHeader from "@/components/financials/PageHeader";
import ValuationCard from "@/components/financials/ValuationCard";
import FinancialTable from "@/components/financials/FinancialTable";
import { FinancialsData } from "@/types/financials";

interface ApiError {
  detail: string;
}

export default function TickerAnalysis() {
  const { ticker } = useParams();
  console.log("ticker from params:", ticker);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<FinancialsData | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setData(null);

      try {
        const response = await fetch(
          `http://localhost:8000/financials?ticker=${encodeURIComponent(ticker?.toString().toUpperCase() || "")}`
        );

        if (!response.ok) {
          const errorData: ApiError = await response.json();
          throw new Error(errorData.detail || `Request failed with status ${response.status}`);
        }

        const result: FinancialsData = await response.json();
        console.log("stockData:", JSON.stringify(result.stockData, null, 2));
        console.log("valuationRatios:", JSON.stringify(result.valuationRatios, null, 2));
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An unexpected error occurred");
      } finally {
        setLoading(false);
      }
    };

    if (ticker) {
      fetchData();
    }
  }, [ticker]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <div className="flex flex-col items-center gap-4 py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-900 dark:border-zinc-700 dark:border-t-zinc-100" />
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Analyzing {ticker?.toString().toUpperCase()}...
          </p>
          <p className="text-xs text-zinc-400 dark:text-zinc-500">
            This may take 30-60 seconds on first run
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <div className="w-full max-w-md rounded-lg border border-red-200 bg-red-50 px-4 py-3 dark:border-red-900 dark:bg-red-950">
          <p className="text-sm font-medium text-red-800 dark:text-red-200">Error</p>
          <p className="mt-1 text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      </div>
    );
  }

  if (data) {
    return (
      <div className="min-h-screen bg-[#09090b]">
        <main className="mx-auto w-full max-w-4xl px-6 py-12">
          <PageHeader ticker={ticker as string} />
          <ValuationCard data={data} />
          <FinancialTable data={data} />
          <details className="mt-8">
            <summary className="cursor-pointer font-mono text-sm text-[#52525b] hover:text-[#71717a]">
              View raw JSON response
            </summary>
            <pre className="mt-2 max-h-96 overflow-auto rounded-lg border border-[#27272a] bg-[#111113] p-4 font-mono text-xs text-[#71717a]">
              {JSON.stringify(data, null, 2)}
            </pre>
          </details>
        </main>
      </div>
    );
  }

  return null;
}
