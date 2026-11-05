export type EntityKind =
  | "syndicate"
  | "broker"
  | "risk"
  | "slip"
  | "policy"
  | "claim"
  | "line"
  | "fund"
  | "admin";

export interface ReadMeta {
  atHeight: number;
  blockHash: string;
  source: "explore" | "signedDeploy";
  deployId: string | null;
}

export interface Receipt {
  deployId: string;
  finalized: boolean;
  blockHash: string | null;
  blockNumber: number;
  termBytes: number;
  status: string;
}

export interface ReadEnvelope<T> {
  ok: true;
  data: T;
  read: ReadMeta;
}

export interface WriteEnvelope<T> {
  ok: true;
  data: T;
  deploy: Receipt;
}

export interface RefusalEnvelope {
  ok: false;
  code: string;
  message: string;
  refusal?: string;
  deploy?: Receipt;
  deployId?: string | null;
}

export type Envelope<T> = ReadEnvelope<T> | WriteEnvelope<T> | RefusalEnvelope;

/** A contract state map. Optional fields are absent when the chain has `Nil`. */
export type State = Record<string, unknown>;

export interface ResolvedComponent {
  uri: string;
  version: number;
}

export interface ComponentReport {
  ok: boolean;
  components: Record<string, ResolvedComponent>;
  message?: string;
}

export interface SyndicateState extends State {
  id?: string;
  uri?: string;
  ownerId?: string;
  managerId?: string;
  name?: string;
  assetId?: string;
  capital?: number;
  committed?: number;
  written?: number;
  premiums?: number;
  claimsPaid?: number;
  members?: Record<string, { contributed?: number; withdrawn?: number }>;
  quotes?: Record<string, State>;
  lines?: Record<string, State>;
  riskAppetite?: string[];
  status?: string;
  nonce?: number;
}

export interface BrokerState extends State {
  id?: string;
  uri?: string;
  ownerId?: string;
  name?: string;
  licenceHash?: string;
  credentialUri?: string;
  commissionBps?: number;
  classes?: string[];
  slips?: Record<string, string>;
  status?: string;
}

export interface RiskState extends State {
  id?: string;
  uri?: string;
  insured?: string;
  broker?: string;
  class?: string;
  assetRef?: State;
  declaredValue?: number;
  requestedLimit?: number;
  requestedDeductible?: number;
  periodStart?: number;
  periodEnd?: number;
  evidence?: State[];
  triTest?: State;
  assessment?: State;
  status?: string;
  slipUri?: string | null;
}

export interface SlipState extends State {
  id?: string;
  uri?: string;
  riskId?: string;
  riskUri?: string;
  insured?: string;
  broker?: string;
  brokerOwner?: string;
  class?: string;
  assetId?: string;
  terms?: State;
  termsHash?: string;
  premiumTotal?: number;
  funded?: number;
  shares?: Record<string, State>;
  lead?: string | null;
  second?: string | null;
  insuredAccepted?: boolean;
  expiryHeight?: number;
  status?: string;
  policyUri?: string | null;
}

export interface PolicyState extends State {
  id?: string;
  uri?: string;
  slipId?: string;
  riskId?: string;
  insured?: string;
  broker?: string;
  brokerOwner?: string;
  class?: string;
  assetId?: string;
  terms?: State;
  premiumTotal?: number;
  lines?: State[];
  aggregateLimit?: number;
  aggregatePaid?: number;
  aggregateRemaining?: number;
  perClaimLimit?: number;
  deductible?: number;
  claims?: Record<string, State>;
  distributed?: boolean;
  status?: string;
}

export interface ClaimState extends State {
  id?: string;
  uri?: string;
  policyId?: string;
  policyUri?: string;
  insured?: string;
  broker?: string;
  lossHeight?: number;
  claimedAmount?: number;
  evidence?: State[];
  classification?: State;
  assessment?: State;
  agreement?: State;
  leadManager?: string | null;
  secondManager?: string | null;
  status?: string;
  agreedAmount?: number;
  paid?: number;
  fundCover?: number;
  oracleRef?: State | null;
}

export interface LineState extends State {
  lineId?: string;
  policy?: string;
  syndicate?: string;
  shareBps?: number;
  exposure?: number;
  status?: string;
  credited?: number;
  paid?: number;
  paidFor?: Record<string, number>;
}

export interface FundState extends State {
  assetId?: string;
  balance?: number;
  levyBps?: number;
  maxCoverPerClaim?: number;
  maxCoverBps?: number;
  contributions?: Record<string, number>;
  covers?: Record<string, State>;
  govNonce?: number;
  admins?: string[];
  threshold?: number;
}

export interface AdminState extends State {
  admins?: string[];
  threshold?: number;
  nonce?: number;
  pausedAll?: boolean;
}

export interface CatalogueEntry {
  kind: EntityKind;
  uri: string;
  label: string;
  detail?: string;
  class?: string;
  insured?: string;
  broker?: string;
  updatedAtHeight?: number;
}

export interface Catalogue {
  schema?: string;
  networkId?: string;
  shard?: string;
  root?: string;
  generatedAt?: string;
  entries?: CatalogueEntry[];
}

export interface JournalEntry {
  id: string;
  kind: string;
  uri?: string;
  related?: string;
  opId?: string;
  deployId?: string;
  blockNumber?: number;
  status: "submitted" | "finalized" | "refused" | "failed" | "unknown";
  refusal?: string;
  summary: string;
  createdAt: number;
}

export interface StoredKeystore {
  address: string;
  document: string;
  label: string;
  createdAt: number;
}

export interface Capability {
  allowed: boolean;
  reason: string;
}
