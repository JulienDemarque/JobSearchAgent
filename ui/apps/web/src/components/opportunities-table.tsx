"use client";

import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from "@tanstack/react-table";
import * as Dialog from "@radix-ui/react-dialog";
import { Eye, RefreshCw, X } from "lucide-react";
import {
  useDeferredValue,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Opportunity,
  OpportunityStatus,
  listOpportunities,
  updateOpportunity,
} from "@/lib/backend-api";
import { cn } from "@/lib/utils";
import { useStreamContext } from "@/providers/Stream";

const OPPORTUNITY_STATUSES: OpportunityStatus[] = [
  "new",
  "interested",
  "applied",
  "interviewing",
  "interviewed",
  "offer",
  "rejected",
  "archived",
];

function formatStatusLabel(status: OpportunityStatus) {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function statusClassName(status: Opportunity["status"]) {
  switch (status) {
    case "applied":
    case "interviewing":
    case "offer":
      return "bg-emerald-50 text-emerald-700 ring-emerald-600/20";
    case "interviewed":
      return "bg-violet-50 text-violet-700 ring-violet-600/20";
    case "rejected":
    case "archived":
      return "bg-gray-50 text-gray-600 ring-gray-500/20";
    case "interested":
      return "bg-blue-50 text-blue-700 ring-blue-600/20";
    default:
      return "bg-amber-50 text-amber-700 ring-amber-600/20";
  }
}

function MetadataPreview({ metadata }: { metadata: Record<string, unknown> }) {
  if (!Object.keys(metadata).length) {
    return <span className="text-muted-foreground">No metadata</span>;
  }

  return (
    <pre className="max-h-48 overflow-auto rounded-md bg-muted p-3 text-xs leading-relaxed text-muted-foreground">
      {JSON.stringify(metadata, null, 2)}
    </pre>
  );
}

export function OpportunitiesTable() {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [search, setSearch] = useState("");
  const [appliedFilter, setAppliedFilter] = useState<"all" | "yes" | "no">(
    "all",
  );
  const [statusFilter, setStatusFilter] = useState<"all" | OpportunityStatus>(
    "all",
  );
  const [minimumScore, setMinimumScore] = useState("");
  const [selectedOpportunity, setSelectedOpportunity] =
    useState<Opportunity | null>(null);
  const deferredSearch = useDeferredValue(search);
  const stream = useStreamContext();
  const queryClient = useQueryClient();
  const wasStreaming = useRef(false);
  const opportunitiesQuery = useQuery({
    queryKey: ["opportunities"],
    queryFn: listOpportunities,
    refetchInterval: 10_000,
  });
  const updateOpportunityMutation = useMutation({
    mutationFn: ({
      opportunity,
      status,
    }: {
      opportunity: Opportunity;
      status: OpportunityStatus;
    }) =>
      updateOpportunity(opportunity.id, {
        status,
        ...(status === "applied" ? { applied: true } : {}),
      }),
    onSuccess: (updatedOpportunity) => {
      queryClient.setQueryData<Opportunity[]>(["opportunities"], (current) =>
        current?.map((opportunity) =>
          opportunity.id === updatedOpportunity.id
            ? updatedOpportunity
            : opportunity,
        ),
      );
      setSelectedOpportunity(updatedOpportunity);
    },
  });

  useEffect(() => {
    if (stream.isLoading) {
      wasStreaming.current = true;
      return;
    }

    if (!wasStreaming.current) return;
    wasStreaming.current = false;
    void queryClient.invalidateQueries({ queryKey: ["opportunities"] });
  }, [queryClient, stream.isLoading]);

  const columns = useMemo<ColumnDef<Opportunity>[]>(
    () => [
      {
        accessorKey: "title",
        header: "Role",
        cell: ({ row }) => (
          <div className="flex min-w-0 items-start gap-2">
            <button
              type="button"
              onClick={() => setSelectedOpportunity(row.original)}
              className="mt-0.5 cursor-pointer rounded-sm text-muted-foreground hover:text-foreground"
              aria-label="Open opportunity details"
            >
              <Eye className="size-4" />
            </button>
            <div className="min-w-0">
              <div className="truncate font-medium text-foreground">
                {row.original.title || "Untitled role"}
              </div>
              {row.original.url ? (
                <a
                  href={row.original.url}
                  target="_blank"
                  rel="noreferrer"
                  className="block truncate text-xs text-muted-foreground hover:text-foreground"
                >
                  {row.original.url}
                </a>
              ) : null}
            </div>
          </div>
        ),
      },
      {
        accessorKey: "company",
        header: "Company",
        cell: ({ row }) => row.original.company || "-",
      },
      {
        accessorKey: "location",
        header: "Location",
        cell: ({ row }) => row.original.location || "-",
      },
      {
        accessorKey: "score",
        header: "Score",
        cell: ({ row }) => (
          <span className="font-medium tabular-nums">
            {row.original.score == null ? "-" : `${row.original.score}/25`}
          </span>
        ),
      },
      {
        accessorKey: "applied",
        header: "Applied",
        cell: ({ row }) => (
          <span
            className={cn(
              "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset",
              row.original.applied
                ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20"
                : "bg-gray-50 text-gray-600 ring-gray-500/20",
            )}
          >
            {row.original.applied ? "Yes" : "No"}
          </span>
        ),
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => (
          <span
            className={cn(
              "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset",
              statusClassName(row.original.status),
            )}
          >
            {row.original.status}
          </span>
        ),
      },
      {
        accessorKey: "updated_at",
        header: "Updated",
        cell: ({ row }) => formatDate(row.original.updated_at),
      },
    ],
    [],
  );

  const filteredOpportunities = useMemo(() => {
    const normalizedSearch = deferredSearch.trim().toLowerCase();
    const minimumScoreValue = minimumScore ? Number(minimumScore) : null;

    return (opportunitiesQuery.data ?? []).filter((opportunity) => {
      if (appliedFilter === "yes" && !opportunity.applied) return false;
      if (appliedFilter === "no" && opportunity.applied) return false;
      if (statusFilter !== "all" && opportunity.status !== statusFilter) {
        return false;
      }
      if (
        minimumScoreValue !== null &&
        Number.isFinite(minimumScoreValue) &&
        (opportunity.score ?? -1) < minimumScoreValue
      ) {
        return false;
      }

      if (!normalizedSearch) return true;

      return [
        opportunity.title,
        opportunity.company,
        opportunity.location,
        opportunity.url,
        opportunity.status,
      ]
        .filter(Boolean)
        .some((value) => value?.toLowerCase().includes(normalizedSearch));
    });
  }, [
    appliedFilter,
    deferredSearch,
    minimumScore,
    opportunitiesQuery.data,
    statusFilter,
  ]);

  const table = useReactTable({
    data: filteredOpportunities,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <Card className="h-full gap-4 overflow-hidden py-0">
      <CardHeader className="border-b px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>Opportunities</CardTitle>
            <CardDescription>
              Jobs tracked by the agent. Refreshes after chat runs and every 10
              seconds.
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => opportunitiesQuery.refetch()}
            disabled={opportunitiesQuery.isFetching}
          >
            <RefreshCw
              className={cn(
                "size-4",
                opportunitiesQuery.isFetching && "animate-spin",
              )}
            />
            Refresh
          </Button>
        </div>
        <div className="grid gap-2 pt-3 md:grid-cols-[minmax(0,1fr)_120px_140px_120px]">
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search roles, companies, locations..."
            className="bg-background"
          />
          <select
            value={appliedFilter}
            onChange={(event) =>
              setAppliedFilter(event.target.value as "all" | "yes" | "no")
            }
            className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-xs"
          >
            <option value="all">All applied</option>
            <option value="yes">Applied</option>
            <option value="no">Not applied</option>
          </select>
          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(event.target.value as "all" | OpportunityStatus)
            }
            className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-xs"
          >
            <option value="all">All statuses</option>
            {OPPORTUNITY_STATUSES.map((status) => (
              <option key={status} value={status}>
                {formatStatusLabel(status)}
              </option>
            ))}
          </select>
          <Input
            type="number"
            min={0}
            max={25}
            value={minimumScore}
            onChange={(event) => setMinimumScore(event.target.value)}
            placeholder="Min score"
            className="bg-background"
          />
        </div>
      </CardHeader>
      <CardContent className="min-h-0 flex-1 overflow-auto p-0">
        {opportunitiesQuery.isError ? (
          <div className="p-4 text-sm text-destructive">
            {(opportunitiesQuery.error as Error).message}
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 z-10 border-b bg-background text-xs uppercase text-muted-foreground">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="whitespace-nowrap px-4 py-3 font-medium"
                    >
                      {header.isPlaceholder ? null : (
                        <button
                          type="button"
                          className="text-left hover:text-foreground"
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                          {{
                            asc: " ↑",
                            desc: " ↓",
                          }[header.column.getIsSorted() as string] ?? null}
                        </button>
                      )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y">
              {table.getRowModel().rows.length ? (
                table.getRowModel().rows.map((row) => (
                  <tr key={row.id} className="hover:bg-muted/40">
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="max-w-64 px-4 py-3">
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="px-4 py-10 text-center text-sm text-muted-foreground"
                  >
                    {opportunitiesQuery.isLoading
                      ? "Loading opportunities..."
                      : "No opportunities yet. Paste jobs into chat to get started."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </CardContent>
      <Dialog.Root
        open={selectedOpportunity !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedOpportunity(null);
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 flex max-h-[85vh] w-[min(900px,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-lg border bg-background shadow-xl">
            <div className="flex items-start justify-between gap-4 border-b p-5">
              <div className="min-w-0">
                <Dialog.Title className="truncate text-lg font-semibold">
                  {selectedOpportunity?.title || "Untitled role"}
                </Dialog.Title>
                <Dialog.Description className="mt-1 text-sm text-muted-foreground">
                  {[selectedOpportunity?.company, selectedOpportunity?.location]
                    .filter(Boolean)
                    .join(" · ") || "Opportunity details"}
                </Dialog.Description>
              </div>
              <Dialog.Close asChild>
                <Button variant="ghost" size="icon" aria-label="Close details">
                  <X className="size-4" />
                </Button>
              </Dialog.Close>
            </div>
            {selectedOpportunity ? (
              <div className="min-h-0 overflow-auto p-5">
                <div className="mb-5 flex flex-wrap gap-2 text-sm">
                  <span
                    className={cn(
                      "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset",
                      statusClassName(selectedOpportunity.status),
                    )}
                  >
                    {selectedOpportunity.status}
                  </span>
                  <span className="inline-flex items-center rounded-md bg-muted px-2 py-1 text-xs font-medium text-muted-foreground">
                    {selectedOpportunity.score == null
                      ? "No score"
                      : `${selectedOpportunity.score}/25`}
                  </span>
                  <span
                    className={cn(
                      "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset",
                      selectedOpportunity.applied
                        ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20"
                        : "bg-gray-50 text-gray-600 ring-gray-500/20",
                    )}
                  >
                    {selectedOpportunity.applied ? "Applied" : "Not applied"}
                  </span>
                </div>

                <div className="mb-5">
                  <h4 className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
                    Quick status
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {OPPORTUNITY_STATUSES.map((status) => (
                      <Button
                        key={status}
                        type="button"
                        variant={
                          selectedOpportunity.status === status
                            ? "default"
                            : "outline"
                        }
                        size="sm"
                        disabled={
                          updateOpportunityMutation.isPending ||
                          selectedOpportunity.status === status
                        }
                        onClick={() =>
                          updateOpportunityMutation.mutate({
                            opportunity: selectedOpportunity,
                            status,
                          })
                        }
                      >
                        {formatStatusLabel(status)}
                      </Button>
                    ))}
                  </div>
                  {updateOpportunityMutation.isError ? (
                    <p className="mt-2 text-sm text-destructive">
                      {(updateOpportunityMutation.error as Error).message}
                    </p>
                  ) : null}
                </div>

                {selectedOpportunity.url ? (
                  <a
                    href={selectedOpportunity.url}
                    target="_blank"
                    rel="noreferrer"
                    className="mb-5 block truncate text-sm text-blue-600 hover:text-blue-800"
                  >
                    {selectedOpportunity.url}
                  </a>
                ) : null}

                <div className="grid gap-5 text-sm lg:grid-cols-2">
                  <section className="space-y-4">
                    <div>
                      <h4 className="text-xs font-semibold uppercase text-muted-foreground">
                        Score reason
                      </h4>
                      <p className="mt-1 whitespace-pre-wrap text-foreground">
                        {selectedOpportunity.score_reason ||
                          "No score reason yet."}
                      </p>
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold uppercase text-muted-foreground">
                        Description
                      </h4>
                      <p className="mt-1 max-h-72 overflow-auto whitespace-pre-wrap text-muted-foreground">
                        {selectedOpportunity.description ||
                          "No description yet."}
                      </p>
                    </div>
                  </section>
                  <section>
                    <h4 className="mb-1 text-xs font-semibold uppercase text-muted-foreground">
                      Raw metadata
                    </h4>
                    <MetadataPreview
                      metadata={selectedOpportunity.raw_metadata ?? {}}
                    />
                  </section>
                </div>
              </div>
            ) : null}
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </Card>
  );
}

