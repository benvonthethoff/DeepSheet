export interface DerivedEntry {
  year: number;
  fcf: number | null;
  grossMarginPct: number | null;
  revenueGrowthPct: number | null;
}

export interface Signal {
  year: number;
  flags: string[];
}

export interface DataEntry {
  year: number;
  val: number | null;
}

export interface StockData {
  price: number | null;
  marketCap: number | null;
  peRatio: number | null;
  currency: string | null;
}

export interface ValuationRatios {
  peRatio: number | null;
  priceFCF: number | null;
}

export interface FinancialsData {
  ticker: string;
  derived: DerivedEntry[];
  signals: {
    revenueSignals: Signal[];
    marginSignals: Signal[];
    fcfSignals: Signal[];
  };
  stockData: StockData;
  valuationRatios: ValuationRatios;
  NetIncomeLoss: DataEntry[];
  PaymentsToAcquirePropertyPlantAndEquipment: DataEntry[];
  [key: string]: unknown;
}
