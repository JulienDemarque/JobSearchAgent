export type OpportunityStatus =
  | "new"
  | "interested"
  | "rejected"
  | "applied"
  | "interviewing"
  | "interviewed"
  | "offer"
  | "archived";

export type Opportunity = {
  id: string;
  url: string | null;
  source: string | null;
  title: string | null;
  company: string | null;
  location: string | null;
  description: string;
  score: number | null;
  score_reason: string | null;
  status: OpportunityStatus;
  applied: boolean;
  applied_at: string | null;
  profile_version: number | null;
  raw_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type OpportunityUpdate = Partial<{
  url: string | null;
  source: string | null;
  title: string | null;
  company: string | null;
  location: string | null;
  description: string;
  score: number | null;
  score_reason: string | null;
  status: OpportunityStatus;
  applied: boolean;
  raw_metadata: Record<string, unknown>;
}>;

const DEFAULT_BACKEND_API_URL = "http://localhost:18080";

export function getBackendApiUrl() {
  return (
    process.env.NEXT_PUBLIC_BACKEND_API_URL?.replace(/\/$/, "") ??
    DEFAULT_BACKEND_API_URL
  );
}

export async function listOpportunities(): Promise<Opportunity[]> {
  const response = await fetch(`${getBackendApiUrl()}/opportunities`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to load opportunities: ${response.status}`);
  }

  return response.json();
}

export async function updateOpportunity(
  opportunityId: string,
  payload: OpportunityUpdate,
): Promise<Opportunity> {
  const response = await fetch(
    `${getBackendApiUrl()}/opportunities/${opportunityId}`,
    {
      method: "PATCH",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to update opportunity: ${response.status}`);
  }

  return response.json();
}

